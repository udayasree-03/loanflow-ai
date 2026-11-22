import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MortgageDocumentSummary(BaseModel):
    id: uuid.UUID
    document_type: str
    file_name: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanApplicationBase(BaseModel):
    borrower_name: str = Field(..., min_length=1, max_length=255, description="Full name of primary borrower")
    borrower_email: str = Field(
        ...,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        max_length=255,
        description="Borrower email address",
    )
    borrower_phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    loan_amount: Decimal = Field(..., gt=0, decimal_places=2, description="Requested mortgage loan amount")
    property_address: Optional[str] = Field(None, max_length=500, description="Subject property address")
    notes: Optional[str] = Field(None, description="Underwriting notes or loan comments")


class LoanApplicationCreate(LoanApplicationBase):
    pass


class LoanApplicationUpdate(BaseModel):
    borrower_name: Optional[str] = Field(None, min_length=1, max_length=255)
    borrower_email: Optional[str] = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    borrower_phone: Optional[str] = Field(None, max_length=50)
    loan_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    property_address: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(
        None,
        pattern=r"^(draft|submitted|processing|underwritten|approved|rejected)$",
        description="Allowed underwriting workflow status",
    )
    notes: Optional[str] = None


class LoanApplicationResponse(LoanApplicationBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    documents: List[MortgageDocumentSummary] = []

    model_config = ConfigDict(from_attributes=True)


class LoanApplicationListResponse(BaseModel):
    items: List[LoanApplicationResponse]
    total: int
    skip: int
    limit: int
