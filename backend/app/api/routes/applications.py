import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.application import (
    LoanApplicationCreate,
    LoanApplicationListResponse,
    LoanApplicationResponse,
    LoanApplicationUpdate,
)
from app.services import loan_service

router = APIRouter()


@router.post(
    "",
    response_model=LoanApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mortgage application",
    description="Registers a new borrower loan application into the underwriting queue.",
)
async def create_new_application(
    payload: LoanApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> LoanApplicationResponse:
    application = await loan_service.create_application(db, payload)
    return LoanApplicationResponse.model_validate(application)


@router.get(
    "",
    response_model=LoanApplicationListResponse,
    summary="List mortgage loan applications",
    description="Retrieve a paginated list of mortgage applications with optional status filter.",
)
async def get_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. draft, submitted)"),
    db: AsyncSession = Depends(get_db),
) -> LoanApplicationListResponse:
    items, total = await loan_service.list_applications(db, skip=skip, limit=limit, status=status_filter)
    return LoanApplicationListResponse(
        items=[LoanApplicationResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{application_id}",
    response_model=LoanApplicationResponse,
    summary="Get loan application details",
    description="Fetch a single loan application by ID, including metadata of all attached documents.",
)
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LoanApplicationResponse:
    application = await loan_service.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application '{application_id}' not found",
        )
    return LoanApplicationResponse.model_validate(application)


@router.patch(
    "/{application_id}",
    response_model=LoanApplicationResponse,
    summary="Update loan application",
    description="Update borrower details or transition the application through underwriting statuses.",
)
async def update_application_details(
    application_id: uuid.UUID,
    payload: LoanApplicationUpdate,
    db: AsyncSession = Depends(get_db),
) -> LoanApplicationResponse:
    updated = await loan_service.update_application(db, application_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application '{application_id}' not found",
        )
    return LoanApplicationResponse.model_validate(updated)


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete loan application",
    description="Permanently deletes a loan application and cascades removal to attached documents.",
)
async def delete_application_record(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await loan_service.delete_application(db, application_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application '{application_id}' not found",
        )
