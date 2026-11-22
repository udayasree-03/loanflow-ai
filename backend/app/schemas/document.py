import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExtractionResultResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    raw_text: str
    structured_data: Dict[str, Any]
    confidence_score: Optional[float] = None
    page_count: int
    extraction_method: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MortgageDocumentResponse(BaseModel):
    id: uuid.UUID
    loan_application_id: Optional[uuid.UUID] = None
    document_type: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(MortgageDocumentResponse):
    extraction_result: Optional[ExtractionResultResponse] = None


class DocumentListResponse(BaseModel):
    items: List[MortgageDocumentResponse]
    total: int
    skip: int
    limit: int
