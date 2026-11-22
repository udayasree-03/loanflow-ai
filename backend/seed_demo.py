"""Demo data seeding script for LoanFlow AI.

Creates 3 realistic mortgage applications with attached documents:
1. Jane Doe: Prime conforming borrower (High income, low DTI -> APPROVED)
2. David Miller: Discrepancy candidate (W-2 vs Paystub variance > 2% -> REFER_TO_HUMAN)
3. Alex Vance: Stretched borrower (High loan amount, low income -> REJECTED)

Run with:
    python seed_demo.py
"""

import asyncio
import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import sitecustomize  # noqa: F401
from sqlalchemy import select
from app.database.session import async_session_maker
from app.database.models.loan_application import LoanApplication
from app.database.models.mortgage_document import MortgageDocument
from app.database.models.extraction_result import ExtractionResult
from app.services.underwriting_agent import run_underwriting_pipeline


DEMO_APPLICATIONS = [
    {
        "borrower_name": "Jane Doe",
        "borrower_email": "jane.doe@example.com",
        "borrower_phone": "(555) 234-5678",
        "loan_amount": Decimal("320000.00"),
        "property_address": "452 Oakridge Drive, Austin, TX 78701",
        "notes": "First-time homebuyer, 20% down payment.",
        "documents": [
            {
                "document_type": "w2",
                "file_name": "W2_2025_Jane_Doe.pdf",
                "file_path": os.path.join(backend_dir, "uploads", "demo_jane_w2.pdf"),
                "raw_text": (
                    "Form W-2 Wage and Tax Statement 2025\n"
                    "Employer: TechCorp Solutions Inc.\n"
                    "Employer EIN: 12-3456789\n"
                    "Employee: Jane Doe\n"
                    "Box 1 Wages, tips, other comp: $125,000.00\n"
                    "Box 2 Federal income tax withheld: $24,800.00\n"
                    "Box 3 Social security wages: $125,000.00\n"
                    "Box 4 Social security tax withheld: $7,750.00\n"
                    "Box 5 Medicare wages and tips: $125,000.00\n"
                ),
            },
            {
                "document_type": "paystub",
                "file_name": "Paystub_Oct2025_Jane_Doe.pdf",
                "file_path": os.path.join(backend_dir, "uploads", "demo_jane_paystub.pdf"),
                "raw_text": (
                    "Earnings Statement - TechCorp Solutions Inc.\n"
                    "Employee: Jane Doe\n"
                    "Pay Period: 10/01/2025 - 10/14/2025\n"
                    "Pay Frequency: Bi-Weekly\n"
                    "Current Gross Earnings: $4,807.69\n"
                    "YTD Gross Earnings: $96,153.80\n"
                    "Net Pay: $3,450.12\n"
                ),
            },
        ],
    },
    {
        "borrower_name": "David Miller",
        "borrower_email": "david.miller@example.com",
        "borrower_phone": "(555) 876-5432",
        "loan_amount": Decimal("460000.00"),
        "property_address": "884 Bellevue Ridge, Seattle, WA 98101",
        "notes": "Relocating for software engineering management role.",
        "documents": [
            {
                "document_type": "w2",
                "file_name": "W2_2025_David_Miller.pdf",
                "file_path": os.path.join(backend_dir, "uploads", "demo_david_w2.pdf"),
                "raw_text": (
                    "Form W-2 Wage and Tax Statement 2025\n"
                    "Employer: CloudScale Systems LLC\n"
                    "Employee: David Miller\n"
                    "Box 1 Wages, tips, other comp: $155,000.00\n"
                    "Box 2 Federal income tax withheld: $32,100.00\n"
                ),
            },
            {
                "document_type": "paystub",
                "file_name": "Paystub_Nov2025_David_Miller.pdf",
                "file_path": os.path.join(backend_dir, "uploads", "demo_david_paystub.pdf"),
                "raw_text": (
                    "Earnings Statement - CloudScale Systems LLC\n"
                    "Employee: David Miller\n"
                    "Pay Frequency: Bi-Weekly\n"
                    "Current Gross Earnings: $4,600.00\n"  # Annualized = $119,600 vs $155k W2 (22.8% variance!)
                    "Net Pay: $3,210.00\n"
                ),
            },
        ],
    },
    {
        "borrower_name": "Alex Vance",
        "borrower_email": "alex.vance@example.com",
        "borrower_phone": "(555) 345-9876",
        "loan_amount": Decimal("680000.00"),
        "property_address": "1200 Sunset Strip, Los Angeles, CA 90028",
        "notes": "Self-employed freelance designer.",
        "documents": [
            {
                "document_type": "w2",
                "file_name": "W2_2025_Alex_Vance.pdf",
                "file_path": os.path.join(backend_dir, "uploads", "demo_alex_w2.pdf"),
                "raw_text": (
                    "Form W-2 Wage and Tax Statement 2025\n"
                    "Employer: Studio Creative Works\n"
                    "Employee: Alex Vance\n"
                    "Box 1 Wages, tips, other comp: $48,000.00\n"
                    "Box 2 Federal income tax withheld: $5,200.00\n"
                ),
            }
        ],
    },
]


async def seed_database():
    print("🌱 Connecting to PostgreSQL database on port 5433...")
    async with async_session_maker() as db:
        for data in DEMO_APPLICATIONS:
            # Check if borrower already exists
            existing = await db.execute(
                select(LoanApplication).where(LoanApplication.borrower_email == data["borrower_email"])
            )
            app = existing.scalar_one_or_none()

            if app:
                print(f"ℹ️  Application for '{data['borrower_name']}' already exists ({app.id}). Skipping.")
                continue

            # Create loan application
            app = LoanApplication(
                borrower_name=data["borrower_name"],
                borrower_email=data["borrower_email"],
                borrower_phone=data["borrower_phone"],
                loan_amount=data["loan_amount"],
                property_address=data["property_address"],
                status="submitted",
                notes=data["notes"],
            )
            db.add(app)
            await db.flush()

            # Create documents and extraction results
            for doc_info in data["documents"]:
                doc = MortgageDocument(
                    loan_application_id=app.id,
                    document_type=doc_info["document_type"],
                    file_name=doc_info["file_name"],
                    file_path=doc_info["file_path"],
                    file_size_bytes=len(doc_info["raw_text"].encode("utf-8")),
                    mime_type="application/pdf",
                    status="extracted",
                )
                db.add(doc)
                await db.flush()

                ext = ExtractionResult(
                    document_id=doc.id,
                    raw_text=doc_info["raw_text"],
                    structured_data={"seeded": True, "document_type": doc_info["document_type"]},
                    confidence_score=0.98,
                    page_count=1,
                    extraction_method="pymupdf",
                    status="success",
                )
                db.add(ext)

            print(f"✅ Created application for '{data['borrower_name']}' with {len(data['documents'])} documents.")

        await db.commit()
    print("🎉 Demo data seeding complete! Refresh your frontend at http://localhost:5173.")


if __name__ == "__main__":
    asyncio.run(seed_database())
