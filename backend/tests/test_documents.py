import io
import uuid
import pymupdf
import pytest
from fastapi.testclient import TestClient


def create_sample_w2_pdf_bytes() -> bytes:
    """Generate a clean synthetic W-2 PDF in memory using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)  # Standard letter size
    sample_text = (
        "Form W-2 Wage and Tax Statement 2025\n"
        "Copy B - To Be Filed With Employee's Federal Tax Return\n\n"
        "Employer Identification Number (EIN): 12-3456789\n"
        "Employer Name: Initech Corporation\n"
        "Employer Address: 4120 Freemont Ave, Austin, TX 78701\n\n"
        "Employee SSN: ***-**-4589\n"
        "Employee Name: Peter Gibbons\n"
        "Employee Address: 1201 Elm St, Austin, TX 78704\n\n"
        "Box 1 Wages, tips, other comp: $94,500.00\n"
        "Box 2 Federal income tax withheld: $14,200.00\n"
        "Box 3 Social security wages: $94,500.00\n"
        "Box 4 Social security tax withheld: $5,859.00\n"
        "Box 5 Medicare wages and tips: $94,500.00\n"
        "Box 6 Medicare tax withheld: $1,370.25\n"
    )
    page.insert_text((50, 80), sample_text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_upload_w2_pdf_and_extraction(client: TestClient) -> None:
    """Upload a synthetic W-2 PDF, verify 201 response, automatic classification, and extracted text."""
    pdf_bytes = create_sample_w2_pdf_bytes()
    files = {"file": ("w2_peter_gibbons.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["file_name"] == "w2_peter_gibbons.pdf"
    assert data["document_type"] == "w2"
    assert data["status"] == "extracted"
    assert data["mime_type"] == "application/pdf"

    # Verify extraction output
    extraction = data["extraction_result"]
    assert extraction is not None
    assert extraction["page_count"] == 1
    assert extraction["extraction_method"] == "pymupdf"
    assert "Initech Corporation" in extraction["raw_text"]
    assert "Box 1 Wages, tips, other comp: $94,500.00" in extraction["raw_text"]
    assert extraction["confidence_score"] >= 0.90


def test_upload_invalid_mime_type_rejected(client: TestClient) -> None:
    """Verify that uploading an unsupported file type returns HTTP 400 Bad Request."""
    fake_script = b"#!/bin/bash\necho 'hello'"
    files = {"file": ("script.sh", io.BytesIO(fake_script), "application/x-sh")}

    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Disallowed file type" in response.json()["detail"]


def test_document_lifecycle_and_download(client: TestClient) -> None:
    """Verify document upload, detail retrieval, download, and deletion lifecycle."""
    pdf_bytes = create_sample_w2_pdf_bytes()
    files = {"file": ("paystub_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data_form = {"document_type": "paystub"}

    # 1. Upload
    upload_res = client.post("/api/v1/documents/upload", files=files, data=data_form)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 2. Get Detail
    detail_res = client.get(f"/api/v1/documents/{doc_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == doc_id
    assert detail_res.json()["document_type"] == "paystub"

    # 3. List
    list_res = client.get("/api/v1/documents?limit=10")
    assert list_res.status_code == 200
    assert any(item["id"] == doc_id for item in list_res.json()["items"])

    # 4. Download
    download_res = client.get(f"/api/v1/documents/{doc_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert len(download_res.content) > 0

    # 5. Delete
    delete_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_res.status_code == 204

    # 6. Verify 404 after deletion
    verify_res = client.get(f"/api/v1/documents/{doc_id}")
    assert verify_res.status_code == 404
