import logging
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.loan_application import LoanApplication
from app.schemas.application import LoanApplicationCreate, LoanApplicationUpdate

logger = logging.getLogger("loanflow.services.loan")


async def create_application(db: AsyncSession, data: LoanApplicationCreate) -> LoanApplication:
    """Create and persist a new loan application record."""
    application = LoanApplication(
        borrower_name=data.borrower_name,
        borrower_email=data.borrower_email,
        borrower_phone=data.borrower_phone,
        loan_amount=data.loan_amount,
        property_address=data.property_address,
        notes=data.notes,
        status="draft",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    logger.info("Created loan application with ID: %s for borrower: %s", application.id, application.borrower_name)
    return application


async def get_application_by_id(db: AsyncSession, application_id: uuid.UUID) -> Optional[LoanApplication]:
    """Fetch a single loan application by UUID with its documents preloaded."""
    stmt = (
        select(LoanApplication)
        .options(selectinload(LoanApplication.documents))
        .where(LoanApplication.id == application_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_applications(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
) -> Tuple[List[LoanApplication], int]:
    """List loan applications with pagination and optional status filter."""
    query = select(LoanApplication).options(selectinload(LoanApplication.documents))
    count_query = select(func.count(LoanApplication.id))

    if status:
        query = query.where(LoanApplication.status == status)
        count_query = count_query.where(LoanApplication.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(LoanApplication.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def update_application(
    db: AsyncSession,
    application_id: uuid.UUID,
    data: LoanApplicationUpdate,
) -> Optional[LoanApplication]:
    """Apply partial update to an existing loan application."""
    application = await get_application_by_id(db, application_id)
    if not application:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(application, field, value)

    await db.commit()
    await db.refresh(application)
    logger.info("Updated loan application %s with fields: %s", application_id, list(update_dict.keys()))
    return application


async def delete_application(db: AsyncSession, application_id: uuid.UUID) -> bool:
    """Delete a loan application record (cascading deletes to attached documents)."""
    application = await get_application_by_id(db, application_id)
    if not application:
        return False

    await db.delete(application)
    await db.commit()
    logger.info("Deleted loan application with ID: %s", application_id)
    return True
