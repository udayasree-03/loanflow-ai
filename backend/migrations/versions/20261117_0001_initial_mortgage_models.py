"""create initial mortgage models

Revision ID: 20261117_0001
Revises: 
Create Date: 2026-11-17 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261117_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create loan_applications table
    op.create_table(
        "loan_applications",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("borrower_name", sa.String(length=255), nullable=False),
        sa.Column("borrower_email", sa.String(length=255), nullable=False),
        sa.Column("borrower_phone", sa.String(length=50), nullable=True),
        sa.Column("loan_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("property_address", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_loan_applications")),
    )
    op.create_index(
        op.f("ix_loan_applications_borrower_email"),
        "loan_applications",
        ["borrower_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_loan_applications_status"),
        "loan_applications",
        ["status"],
        unique=False,
    )

    # 2. Create mortgage_documents table
    op.create_table(
        "mortgage_documents",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("loan_application_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["loan_application_id"],
            ["loan_applications.id"],
            name=op.f("fk_mortgage_documents_loan_application_id_loan_applications"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mortgage_documents")),
    )
    op.create_index(
        op.f("ix_mortgage_documents_loan_application_id"),
        "mortgage_documents",
        ["loan_application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mortgage_documents_document_type"),
        "mortgage_documents",
        ["document_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mortgage_documents_status"),
        "mortgage_documents",
        ["status"],
        unique=False,
    )

    # 3. Create extraction_results table
    op.create_table(
        "extraction_results",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column(
            "structured_data",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["mortgage_documents.id"],
            name=op.f("fk_extraction_results_document_id_mortgage_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extraction_results")),
        sa.UniqueConstraint("document_id", name=op.f("uq_extraction_results_document_id")),
    )
    op.create_index(
        op.f("ix_extraction_results_document_id"),
        "extraction_results",
        ["document_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_extraction_results_status"),
        "extraction_results",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("extraction_results")
    op.drop_table("mortgage_documents")
    op.drop_table("loan_applications")
