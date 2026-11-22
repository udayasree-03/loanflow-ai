import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.database.models.extraction_result import ExtractionResult
from app.database.models.mortgage_document import MortgageDocument

logger = logging.getLogger("loanflow.services.extractor")

# Document classification signature patterns
CLASSIFICATION_PATTERNS = {
    "w2": [
        r"form\s+w-2",
        r"wage\s+and\s+tax\s+statement",
        r"social\s+security\s+wages",
        r"medicare\s+wages",
        r"employer\s+identification\s+number",
    ],
    "form_1040": [
        r"form\s+1040",
        r"u\.s\.\s+individual\s+income\s+tax\s+return",
        r"adjusted\s+gross\s+income",
        r"filing\s+status",
        r"internal\s+revenue\s+service",
    ],
    "paystub": [
        r"pay\s*stub",
        r"earnings\s+statement",
        r"pay\s+period",
        r"ytd\s+gross",
        r"net\s+pay",
        r"hourly\s+rate",
    ],
    "bank_statement": [
        r"bank\s+statement",
        r"account\s+summary",
        r"beginning\s+balance",
        r"ending\s+balance",
        r"deposits\s+and\s+additions",
    ],
}


def classify_document_text(text: str) -> str:
    """Heuristic keyword classification of mortgage documents."""
    text_lower = text.lower()
    for doc_type, patterns in CLASSIFICATION_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches >= 2:
            return doc_type
    return "unclassified"


def extract_text_from_pdf(file_path: Path) -> Dict[str, Any]:
    """Extract digital text layer, pages, and metadata using PyMuPDF."""
    doc = pymupdf.open(str(file_path))
    page_count = len(doc)
    pages_text: List[str] = []
    total_chars = 0

    for i in range(page_count):
        page = doc[i]
        page_text = page.get_text("text").strip()
        pages_text.append(f"--- Page {i + 1} ---\n{page_text}")
        total_chars += len(page_text)

    full_text = "\n\n".join(pages_text).strip()
    avg_chars_per_page = total_chars / max(page_count, 1)

    # Scanned detection: if average text per page is low (< 40 characters), PDF is likely an image scan
    is_scanned = avg_chars_per_page < 40 and page_count > 0
    confidence = 0.95 if not is_scanned else 0.40
    method = "pymupdf" if not is_scanned else "needs_ocr"

    detected_type = classify_document_text(full_text)
    pdf_meta = {k: v for k, v in doc.metadata.items() if v} if doc.metadata else {}

    doc.close()

    return {
        "raw_text": full_text,
        "page_count": page_count,
        "confidence_score": confidence,
        "extraction_method": method,
        "is_scanned": is_scanned,
        "detected_type": detected_type,
        "structured_data": {
            "page_count": page_count,
            "total_characters": total_chars,
            "is_scanned_document": is_scanned,
            "detected_type": detected_type,
            "pdf_metadata": pdf_meta,
        },
    }


async def save_and_extract_document(
    db: AsyncSession,
    file: UploadFile,
    loan_application_id: Optional[uuid.UUID] = None,
    document_type_hint: Optional[str] = None,
) -> MortgageDocument:
    """Validate, persist to disk, extract text with PyMuPDF, and save DB records."""
    # 1. Validate MIME type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Disallowed file type '{content_type}'. Allowed: {settings.ALLOWED_MIME_TYPES}",
        )

    # 2. Read file content and check size limit
    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
        )

    # 3. Generate sanitized disk filename & save file
    doc_id = uuid.uuid4()
    original_name = Path(file.filename or "document.pdf").name
    safe_filename = f"{doc_id}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', original_name)}"
    destination_path = settings.upload_path / safe_filename

    destination_path.write_bytes(content)
    logger.info("Saved uploaded file to %s (%d bytes)", destination_path, file_size)

    # 4. Perform extraction
    extraction_status = "extracted"
    raw_text = ""
    structured_data: Dict[str, Any] = {}
    confidence = 0.90
    page_count = 1
    method = "pymupdf"
    detected_type = document_type_hint or "unclassified"

    try:
        if content_type == "application/pdf":
            ext_result = extract_text_from_pdf(destination_path)
            raw_text = ext_result["raw_text"]
            page_count = ext_result["page_count"]
            confidence = ext_result["confidence_score"]
            method = ext_result["extraction_method"]
            structured_data = ext_result["structured_data"]
            if detected_type in (None, "unclassified"):
                detected_type = ext_result["detected_type"]
        else:
            # Image formats (PNG/JPEG/TIFF) flagged for OCR processing
            raw_text = f"Image file staged: {original_name}. Text layer requires OCR processing."
            method = "needs_ocr"
            confidence = 0.50
            structured_data = {"format": content_type, "requires_ocr": True}
    except Exception as exc:
        logger.error("Extraction failed for document %s: %s", doc_id, exc)
        extraction_status = "failed"
        raw_text = f"Extraction failed: {str(exc)}"
        method = "error"
        confidence = 0.0

    # 5. Persist MortgageDocument in database
    doc_record = MortgageDocument(
        id=doc_id,
        loan_application_id=loan_application_id,
        document_type=detected_type,
        file_name=original_name,
        file_path=str(destination_path),
        file_size_bytes=file_size,
        mime_type=content_type,
        status=extraction_status,
    )
    db.add(doc_record)

    # 6. Persist ExtractionResult linked to document
    result_record = ExtractionResult(
        id=uuid.uuid4(),
        document_id=doc_id,
        raw_text=raw_text,
        structured_data=structured_data,
        confidence_score=confidence,
        page_count=page_count,
        extraction_method=method,
        status="success" if extraction_status == "extracted" else "failed",
    )
    db.add(result_record)

    await db.commit()
    await db.refresh(doc_record)

    return doc_record


async def get_document_with_extraction(
    db: AsyncSession,
    document_id: uuid.UUID,
) -> Optional[MortgageDocument]:
    """Retrieve a document along with its preloaded extraction result."""
    stmt = (
        select(MortgageDocument)
        .options(selectinload(MortgageDocument.extraction_result))
        .where(MortgageDocument.id == document_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_documents(
    db: AsyncSession,
    loan_application_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[MortgageDocument], int]:
    """List documents with optional loan application filtering."""
    query = select(MortgageDocument)
    count_query = select(func.count(MortgageDocument.id))

    if loan_application_id:
        query = query.where(MortgageDocument.loan_application_id == loan_application_id)
        count_query = count_query.where(MortgageDocument.loan_application_id == loan_application_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(MortgageDocument.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def delete_document(db: AsyncSession, document_id: uuid.UUID) -> bool:
    """Delete document DB record and remove physical file from disk."""
    doc = await get_document_with_extraction(db, document_id)
    if not doc:
        return False

    # Remove physical file from uploads folder if it exists
    try:
        file_path = Path(doc.file_path)
        if file_path.is_file():
            file_path.unlink()
            logger.info("Deleted physical file: %s", file_path)
    except Exception as exc:
        logger.warning("Could not delete file on disk %s: %s", doc.file_path, exc)

    await db.delete(doc)
    await db.commit()
    return True
