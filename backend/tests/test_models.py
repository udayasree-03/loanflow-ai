import uuid
from decimal import Decimal
from app.database.base import Base
from app.database.models.loan_application import LoanApplication
from app.database.models.mortgage_document import MortgageDocument
from app.database.models.extraction_result import ExtractionResult


def test_metadata_tables_registered() -> None:
    """Verify that all core models are registered in Base.metadata."""
    table_names = list(Base.metadata.tables.keys())
    assert "loan_applications" in table_names
    assert "mortgage_documents" in table_names
    assert "extraction_results" in table_names


def test_loan_application_model_defaults() -> None:
    """Verify default values and attributes on a new LoanApplication."""
    app_id = uuid.uuid4()
    app = LoanApplication(
        id=app_id,
        borrower_name="Jane Doe",
        borrower_email="jane.doe@example.com",
        borrower_phone="555-0199",
        loan_amount=Decimal("450000.00"),
        property_address="123 Maple Street, Austin, TX",
    )

    assert app.id == app_id
    assert app.borrower_name == "Jane Doe"
    assert app.borrower_email == "jane.doe@example.com"
    assert app.loan_amount == Decimal("450000.00")
    assert app.status == "draft"
    assert repr(app) == f"<LoanApplication(id={app_id}, borrower='Jane Doe', status='draft')>"


def test_mortgage_document_relationship() -> None:
    """Verify MortgageDocument model instantiation and relationship back-reference."""
    app_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    app = LoanApplication(
        id=app_id,
        borrower_name="John Smith",
        borrower_email="john.smith@example.com",
        loan_amount=Decimal("320000.00"),
    )

    doc = MortgageDocument(
        id=doc_id,
        loan_application_id=app_id,
        document_type="w2",
        file_name="w2_2025.pdf",
        file_path="uploads/w2_2025.pdf",
        file_size_bytes=1048576,
        mime_type="application/pdf",
        status="uploaded",
    )

    # Wire relationship in-memory
    app.documents.append(doc)

    assert len(app.documents) == 1
    assert app.documents[0].file_name == "w2_2025.pdf"
    assert app.documents[0].document_type == "w2"
    assert doc.loan_application_id == app.id
    assert repr(doc) == f"<MortgageDocument(id={doc_id}, type='w2', file='w2_2025.pdf', status='uploaded')>"


def test_extraction_result_model() -> None:
    """Verify ExtractionResult model instantiation with structured JSON payload."""
    doc_id = uuid.uuid4()
    res_id = uuid.uuid4()

    payload = {
        "employer_name": "Acme Corp",
        "wages_tips_compensation": 98500.00,
        "tax_year": 2025,
        "ssn_masked": "***-**-1234",
    }

    extraction = ExtractionResult(
        id=res_id,
        document_id=doc_id,
        raw_text="W-2 Wage and Tax Statement 2025 Acme Corp Wages: $98,500.00",
        structured_data=payload,
        confidence_score=0.98,
        page_count=1,
        extraction_method="pymupdf",
        status="success",
    )

    assert extraction.id == res_id
    assert extraction.document_id == doc_id
    assert extraction.structured_data["employer_name"] == "Acme Corp"
    assert extraction.structured_data["wages_tips_compensation"] == 98500.00
    assert extraction.confidence_score == 0.98
    assert extraction.status == "success"
    assert repr(extraction) == f"<ExtractionResult(id={res_id}, doc_id={doc_id}, method='pymupdf', status='success')>"
