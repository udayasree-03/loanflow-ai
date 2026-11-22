import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    MortgageDocumentResponse,
)
from app.services import document_extractor

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload mortgage document and extract text",
    description="Uploads a PDF or image mortgage document, extracts its digital text layer via PyMuPDF, and classifies document type.",
)
async def upload_document(
    file: UploadFile = File(..., description="Mortgage document file (PDF, PNG, JPEG, TIFF)"),
    loan_application_id: Optional[uuid.UUID] = Form(None, description="Optional associated loan application UUID"),
    document_type: Optional[str] = Form(None, description="Optional manual type hint (w2, form_1040, paystub, bank_statement)"),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    doc = await document_extractor.save_and_extract_document(
        db=db,
        file=file,
        loan_application_id=loan_application_id,
        document_type_hint=document_type,
    )
    loaded = await document_extractor.get_document_with_extraction(db, doc.id)
    return DocumentDetailResponse.model_validate(loaded)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List mortgage documents",
    description="Retrieve a paginated list of uploaded mortgage documents, optionally filtered by loan application ID.",
)
async def get_documents(
    loan_application_id: Optional[uuid.UUID] = Query(None, description="Filter by loan application UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    items, total = await document_extractor.list_documents(
        db,
        loan_application_id=loan_application_id,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(
        items=[MortgageDocumentResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details & extracted text",
    description="Fetch document metadata along with the raw and structured extraction output.",
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    doc = await document_extractor.get_document_with_extraction(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mortgage document '{document_id}' not found",
        )
    return DocumentDetailResponse.model_validate(doc)


@router.get(
    "/{document_id}/download",
    summary="Download original mortgage file",
    description="Download the raw uploaded document file from secure storage.",
)
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    doc = await document_extractor.get_document_with_extraction(db, document_id)
    if not doc or not Path(doc.file_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File for document '{document_id}' not found on storage",
        )
    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type=doc.mime_type,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete mortgage document",
    description="Permanently removes document record, extraction results, and disk file.",
)
async def delete_document_record(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await document_extractor.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mortgage document '{document_id}' not found",
        )
