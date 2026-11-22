import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.underwriting_agent import run_underwriting_pipeline


@pytest.mark.anyio
async def test_underwriting_pipeline_approved():
    """Tests conforming scenario where DTI <= 43% and W-2 income is verified."""
    app_id = uuid.uuid4()
    docs = [
        {
            "id": str(uuid.uuid4()),
            "document_type": "w2",
            "file_name": "w2_2025.pdf",
            "raw_text": (
                "Form W-2 Wage and Tax Statement 2025\n"
                "Employer: TechCorp Global Solutions LLC\n"
                "Employee: Jane Doe\n"
                "Box 1 Wages, tips, other comp: $120,000.00\n"
                "Box 2 Federal income tax withheld: $22,400.00\n"
            ),
        }
    ]

    result = await run_underwriting_pipeline(
        application_id=app_id,
        borrower_name="Jane Doe",
        borrower_email="jane.doe@example.com",
        loan_amount=300000.0,
        property_value=400000.0,
        monthly_debt=400.0,
        interest_rate_pct=6.5,
        loan_term_years=30,
        documents=docs,
    )

    decision = result["decision"]
    dti = result["dti_analysis"]
    entities = result["financial_entities"]

    assert decision["status"] == "APPROVED"
    assert decision["confidence_score"] >= 0.90
    assert entities["qualifying_monthly_income"] == 10000.0
    assert dti["back_end_dti_pct"] < 43.0
    assert dti["passes_back_end"] is True
    assert len(decision["conditions"]) > 0


@pytest.mark.anyio
async def test_underwriting_pipeline_income_discrepancy_refer():
    """Tests scenario where W-2 and Paystub diverge by > 2%, triggering human review."""
    app_id = uuid.uuid4()
    docs = [
        {
            "id": str(uuid.uuid4()),
            "document_type": "w2",
            "file_name": "w2.pdf",
            "raw_text": "Form W-2\nBox 1 Wages, tips, other comp: $120,000.00\n",
        },
        {
            "id": str(uuid.uuid4()),
            "document_type": "paystub",
            "file_name": "paystub.pdf",
            "raw_text": "Earnings Statement\nPay Frequency: Bi-Weekly\nCurrent Gross Earnings: $3,500.00\n",
        },
    ]

    result = await run_underwriting_pipeline(
        application_id=app_id,
        borrower_name="Jane Doe",
        borrower_email="jane.doe@example.com",
        loan_amount=300000.0,
        property_value=400000.0,
        monthly_debt=400.0,
        documents=docs,
    )

    decision = result["decision"]
    flags = result["discrepancy_flags"]

    assert decision["status"] == "REFER_TO_HUMAN"
    variance_flags = [f for f in flags if f.get("category") == "income_variance"]
    assert len(variance_flags) >= 1
    assert variance_flags[0]["variance_pct"] > 2.0


@pytest.mark.anyio
async def test_underwriting_pipeline_excessive_dti_rejected():
    """Tests scenario where Back-End DTI exceeds 50%, resulting in automatic rejection."""
    app_id = uuid.uuid4()
    docs = [
        {
            "id": str(uuid.uuid4()),
            "document_type": "w2",
            "file_name": "w2.pdf",
            "raw_text": "Form W-2\nBox 1 Wages: $48,000.00\n",  # $4,000/mo income
        }
    ]

    result = await run_underwriting_pipeline(
        application_id=app_id,
        borrower_name="High Debt Borrower",
        borrower_email="debt@example.com",
        loan_amount=500000.0,  # P&I on $500k is > $3,100 alone
        property_value=600000.0,
        monthly_debt=1000.0,  # Total debt will be > $4,000/mo vs $4,000 income -> DTI > 100%
        documents=docs,
    )

    decision = result["decision"]
    dti = result["dti_analysis"]

    assert decision["status"] == "REJECTED"
    assert dti["back_end_dti_pct"] > 50.0
    assert dti["passes_back_end"] is False


@pytest.mark.anyio
async def test_underwriting_pipeline_missing_docs_refer():
    """Tests scenario with zero income documents, triggering REFER_TO_HUMAN."""
    app_id = uuid.uuid4()
    result = await run_underwriting_pipeline(
        application_id=app_id,
        borrower_name="No Docs",
        borrower_email="nodocs@example.com",
        loan_amount=200000.0,
        property_value=250000.0,
        documents=[],
    )

    decision = result["decision"]
    flags = result["discrepancy_flags"]

    assert decision["status"] == "REFER_TO_HUMAN"
    missing_doc_flags = [f for f in flags if f.get("category") == "missing_doc"]
    assert len(missing_doc_flags) >= 1


def test_api_underwriting_lifecycle():
    """End-to-end API test creating application and triggering underwriting endpoint."""
    client = TestClient(app)

    # 1. Create a loan application
    app_payload = {
        "borrower_name": "Michael Corleone",
        "borrower_email": "michael.c@example.com",
        "borrower_phone": "555-0199",
        "loan_amount": 280000.00,
        "property_address": "123 Lake Tahoe Blvd, NV",
    }
    create_resp = client.post("/api/v1/applications", json=app_payload)
    assert create_resp.status_code == 201
    app_data = create_resp.json()
    app_id = app_data["id"]

    # 2. Trigger underwriting via API
    underwrite_payload = {
        "property_value": 375000.00,
        "monthly_debt": 350.00,
        "interest_rate_pct": 6.25,
        "loan_term_years": 30,
    }
    uw_resp = client.post(f"/api/v1/applications/{app_id}/underwrite", json=underwrite_payload)
    assert uw_resp.status_code == 200
    uw_data = uw_resp.json()

    assert uw_data["application_id"] == app_id
    assert uw_data["borrower_name"] == "Michael Corleone"
    assert "decision" in uw_data
    assert "dti_analysis" in uw_data
    assert "status" in uw_data

    # 3. GET current underwriting
    get_uw_resp = client.get(f"/api/v1/applications/{app_id}/underwrite")
    assert get_uw_resp.status_code == 200
    assert get_uw_resp.json()["application_id"] == app_id

    # 4. Underwrite non-existent application returns 404
    fake_id = str(uuid.uuid4())
    fake_resp = client.post(f"/api/v1/applications/{fake_id}/underwrite", json={})
    assert fake_resp.status_code == 404
