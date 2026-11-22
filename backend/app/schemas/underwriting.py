import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class UnderwritingRunRequest(BaseModel):
    """Optional manual overrides or additions when triggering underwriting."""
    property_value: Optional[Decimal] = Field(
        None,
        description="Appraised or estimated property value. If omitted, calculated based on standard LTV.",
        gt=0,
    )
    monthly_debt: Optional[Decimal] = Field(
        None,
        description="Declared monthly non-mortgage debt (auto, credit cards, student loans).",
        ge=0,
    )
    interest_rate_pct: Optional[float] = Field(
        None,
        description="Annual mortgage interest rate percentage (e.g. 6.5 for 6.5%).",
        gt=0,
        le=25,
    )
    loan_term_years: Optional[int] = Field(
        None,
        description="Loan term in years (e.g. 15 or 30).",
        gt=0,
        le=50,
    )


class ExtractedFinancialEntities(BaseModel):
    """Normalized financial entities extracted from uploaded documents."""
    borrower_name: Optional[str] = None
    employer_name: Optional[str] = None
    w2_annual_wages: Optional[float] = None
    w2_federal_tax: Optional[float] = None
    paystub_gross_pay: Optional[float] = None
    paystub_pay_frequency: Optional[str] = None
    paystub_annualized_income: Optional[float] = None
    form_1040_tax_year: Optional[int] = None
    form_1040_total_wages: Optional[float] = None
    form_1040_adjusted_gross_income: Optional[float] = None
    bank_statement_ending_balance: Optional[float] = None
    qualifying_monthly_income: float = 0.0
    income_source_documents: List[str] = Field(default_factory=list)


class DiscrepancyFlag(BaseModel):
    """Discrepancy or anomaly identified across mortgage documents."""
    severity: Literal["low", "medium", "high", "critical"]
    category: str  # "identity", "income_variance", "missing_doc", "guideline_breach"
    field: str
    message: str
    document_a: Optional[str] = None
    value_a: Optional[str] = None
    document_b: Optional[str] = None
    value_b: Optional[str] = None
    variance_pct: Optional[float] = None


class DTIAnalysis(BaseModel):
    """Debt-to-Income and Loan-to-Value metric calculations."""
    loan_amount: float
    property_value: float
    ltv_ratio_pct: float
    qualifying_monthly_income: float
    estimated_monthly_pi: float
    estimated_monthly_escrow: float
    total_monthly_housing_expense: float
    monthly_non_housing_debt: float
    total_monthly_debt: float
    front_end_dti_pct: float
    back_end_dti_pct: float
    max_allowed_dti_pct: float
    passes_front_end: bool
    passes_back_end: bool


class UnderwritingDecision(BaseModel):
    """The final automated underwriting decision."""
    status: Literal["APPROVED", "REFER_TO_HUMAN", "REJECTED"]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)


class UnderwritingResultResponse(BaseModel):
    """Complete response returned by underwriting workflow."""
    application_id: uuid.UUID
    borrower_name: str
    loan_amount: float
    status: Literal["APPROVED", "REFER_TO_HUMAN", "REJECTED"]
    decision: UnderwritingDecision
    dti_analysis: DTIAnalysis
    financial_entities: ExtractedFinancialEntities
    flags: List[DiscrepancyFlag] = Field(default_factory=list)
    reasoning_log: List[str] = Field(default_factory=list)
    document_count: int
    created_at: datetime
