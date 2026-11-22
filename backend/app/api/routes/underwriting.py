import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.loan_application import LoanApplication
from app.database.models.mortgage_document import MortgageDocument
from app.database.session import get_db
from app.schemas.underwriting import (
    DiscrepancyFlag,
    DTIAnalysis,
    ExtractedFinancialEntities,
    UnderwritingDecision,
    UnderwritingResultResponse,
    UnderwritingRunRequest,
)
from app.services.underwriting_agent import run_underwriting_pipeline

router = APIRouter(prefix="/applications", tags=["Underwriting"])
logger = logging.getLogger("loanflow.api.underwriting")


def _format_underwriting_response(
    app_id: uuid.UUID,
    borrower_name: str,
    loan_amount: float,
    result_state: Dict[str, Any],
    doc_count: int,
) -> UnderwritingResultResponse:
    """Formats raw LangGraph state dictionary into validated response schema."""
    decision_dict = result_state.get("decision", {})
    decision = UnderwritingDecision(
        status=decision_dict.get("status", "REFER_TO_HUMAN"),
        confidence_score=decision_dict.get("confidence_score", 0.5),
        summary=decision_dict.get("summary", "Underwriting evaluation completed."),
        key_findings=decision_dict.get("key_findings", []),
        conditions=decision_dict.get("conditions", []),
    )

    dti_dict = result_state.get("dti_analysis", {})
    dti_analysis = DTIAnalysis(
        loan_amount=float(dti_dict.get("loan_amount", loan_amount)),
        property_value=float(dti_dict.get("property_value", 0.0)),
        ltv_ratio_pct=float(dti_dict.get("ltv_ratio_pct", 0.0)),
        qualifying_monthly_income=float(dti_dict.get("qualifying_monthly_income", 0.0)),
        estimated_monthly_pi=float(dti_dict.get("estimated_monthly_pi", 0.0)),
        estimated_monthly_escrow=float(dti_dict.get("estimated_monthly_escrow", 0.0)),
        total_monthly_housing_expense=float(dti_dict.get("total_monthly_housing_expense", 0.0)),
        monthly_non_housing_debt=float(dti_dict.get("monthly_non_housing_debt", 0.0)),
        total_monthly_debt=float(dti_dict.get("total_monthly_debt", 0.0)),
        front_end_dti_pct=float(dti_dict.get("front_end_dti_pct", 0.0)),
        back_end_dti_pct=float(dti_dict.get("back_end_dti_pct", 0.0)),
        max_allowed_dti_pct=float(dti_dict.get("max_allowed_dti_pct", 43.0)),
        passes_front_end=bool(dti_dict.get("passes_front_end", False)),
        passes_back_end=bool(dti_dict.get("passes_back_end", False)),
    )

    entities_dict = result_state.get("financial_entities", {})
    entities = ExtractedFinancialEntities(
        borrower_name=entities_dict.get("borrower_name"),
        employer_name=entities_dict.get("employer_name"),
        w2_annual_wages=entities_dict.get("w2_annual_wages"),
        w2_federal_tax=entities_dict.get("w2_federal_tax"),
        paystub_gross_pay=entities_dict.get("paystub_gross_pay"),
        paystub_pay_frequency=entities_dict.get("paystub_pay_frequency"),
        paystub_annualized_income=entities_dict.get("paystub_annualized_income"),
        form_1040_tax_year=entities_dict.get("form_1040_tax_year"),
        form_1040_total_wages=entities_dict.get("form_1040_total_wages"),
        form_1040_adjusted_gross_income=entities_dict.get("form_1040_adjusted_gross_income"),
        bank_statement_ending_balance=entities_dict.get("bank_statement_ending_balance"),
        qualifying_monthly_income=float(entities_dict.get("qualifying_monthly_income", 0.0)),
        income_source_documents=entities_dict.get("income_source_documents", []),
    )

    raw_flags = result_state.get("discrepancy_flags", [])
    flags: List[DiscrepancyFlag] = [
        DiscrepancyFlag(
            severity=f.get("severity", "low"),
            category=f.get("category", "general"),
            field=f.get("field", ""),
            message=f.get("message", ""),
            document_a=f.get("document_a"),
            value_a=f.get("value_a"),
            document_b=f.get("document_b"),
            value_b=f.get("value_b"),
            variance_pct=f.get("variance_pct"),
        )
        for f in raw_flags
    ]

    return UnderwritingResultResponse(
        application_id=app_id,
        borrower_name=borrower_name,
        loan_amount=loan_amount,
        status=decision.status,
        decision=decision,
        dti_analysis=dti_analysis,
        financial_entities=entities,
        flags=flags,
        reasoning_log=result_state.get("reasoning_log", []),
        document_count=doc_count,
        created_at=datetime.now(timezone.utc),
    )


@router.post(
    "/{application_id}/underwrite",
    response_model=UnderwritingResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute LangGraph underwriting pipeline for an application",
    description="Extracts multi-document financial entities, cross-verifies discrepancies, checks DTI/LTV guidelines, and renders an automated underwriting decision.",
)
async def trigger_application_underwriting(
    application_id: uuid.UUID,
    payload: UnderwritingRunRequest = UnderwritingRunRequest(),
    db: AsyncSession = Depends(get_db),
) -> UnderwritingResultResponse:
    # 1. Fetch loan application
    app_stmt = select(LoanApplication).where(LoanApplication.id == application_id)
    app_result = await db.execute(app_stmt)
    application = app_result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application '{application_id}' not found",
        )

    # 2. Fetch associated documents with extraction results
    docs_stmt = select(MortgageDocument).where(MortgageDocument.loan_application_id == application_id)
    docs_result = await db.execute(docs_stmt)
    documents = docs_result.scalars().all()

    # Format document payloads
    doc_payloads: List[Dict[str, Any]] = []
    for doc in documents:
        raw_text = doc.extraction_result.raw_text if doc.extraction_result else ""
        doc_payloads.append({
            "id": str(doc.id),
            "document_type": doc.document_type,
            "file_name": doc.file_name,
            "raw_text": raw_text,
            "structured_data": doc.extraction_result.structured_data if doc.extraction_result else {},
        })

    # 3. Execute LangGraph workflow
    prop_val = float(payload.property_value) if payload.property_value is not None else None
    monthly_debt = float(payload.monthly_debt) if payload.monthly_debt is not None else None
    loan_amount = float(application.loan_amount)

    underwriting_state = await run_underwriting_pipeline(
        application_id=application.id,
        borrower_name=application.borrower_name,
        borrower_email=application.borrower_email,
        loan_amount=loan_amount,
        documents=doc_payloads,
        property_value=prop_val,
        monthly_debt=monthly_debt,
        interest_rate_pct=payload.interest_rate_pct,
        loan_term_years=payload.loan_term_years,
    )

    # 4. Format response
    response = _format_underwriting_response(
        app_id=application.id,
        borrower_name=application.borrower_name,
        loan_amount=loan_amount,
        result_state=underwriting_state,
        doc_count=len(documents),
    )

    # 5. Persist status and serialized decision in application
    application.status = "underwritten"
    try:
        decision_summary = {
            "decision": response.decision.model_dump(),
            "dti_analysis": response.dti_analysis.model_dump(),
            "flags_count": len(response.flags),
            "last_underwritten_at": datetime.now(timezone.utc).isoformat(),
        }
        application.notes = json.dumps(decision_summary)
    except Exception as e:
        logger.warning(f"Could not serialize decision to notes: {e}")

    await db.commit()
    await db.refresh(application)

    return response


@router.get(
    "/{application_id}/underwrite",
    response_model=UnderwritingResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current or evaluated underwriting assessment for an application",
)
async def get_application_underwriting(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UnderwritingResultResponse:
    # Trigger current underwriting evaluation
    return await trigger_application_underwriting(
        application_id=application_id,
        payload=UnderwritingRunRequest(),
        db=db,
    )
