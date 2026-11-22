import uuid
from decimal import Decimal
from fastapi.testclient import TestClient


def test_create_loan_application_success(client: TestClient) -> None:
    """Verify creating a valid loan application returns HTTP 201 with generated UUID."""
    payload = {
        "borrower_name": "Sarah Connor",
        "borrower_email": "sarah.connor@example.com",
        "borrower_phone": "555-0143",
        "loan_amount": 550000.00,
        "property_address": "42 Cyberdyne Way, Los Angeles, CA",
        "notes": "Conventional 30-year fixed loan request",
    }
    response = client.post("/api/v1/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["borrower_name"] == "Sarah Connor"
    assert data["borrower_email"] == "sarah.connor@example.com"
    assert float(data["loan_amount"]) == 550000.00
    assert data["status"] == "draft"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_loan_application_invalid_payload(client: TestClient) -> None:
    """Verify validation rejection on invalid email and negative loan amount (HTTP 422)."""
    invalid_payload = {
        "borrower_name": "",
        "borrower_email": "not-an-email",
        "loan_amount": -1000.00,
    }
    response = client.post("/api/v1/applications", json=invalid_payload)
    assert response.status_code == 422


def test_get_loan_application_lifecycle(client: TestClient) -> None:
    """Test full CRUD lifecycle: create, get by id, list, patch update, and delete."""
    # 1. Create
    payload = {
        "borrower_name": "Michael Corleone",
        "borrower_email": "michael@corleone.com",
        "loan_amount": 1200000.00,
        "property_address": "110 Long Island Sound, NY",
    }
    create_res = client.post("/api/v1/applications", json=payload)
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    # 2. Get by ID
    get_res = client.get(f"/api/v1/applications/{app_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == app_id
    assert get_res.json()["status"] == "draft"

    # 3. List
    list_res = client.get("/api/v1/applications?limit=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == app_id for item in list_data["items"])

    # 4. Patch Update Status
    patch_res = client.patch(
        f"/api/v1/applications/{app_id}",
        json={"status": "submitted", "notes": "Documents submitted by borrower"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "submitted"
    assert patch_res.json()["notes"] == "Documents submitted by borrower"

    # 5. Delete
    delete_res = client.delete(f"/api/v1/applications/{app_id}")
    assert delete_res.status_code == 204

    # 6. Verify 404 after delete
    verify_res = client.get(f"/api/v1/applications/{app_id}")
    assert verify_res.status_code == 404


def test_get_nonexistent_application_returns_404(client: TestClient) -> None:
    """Verify requesting a non-existent UUID returns HTTP 404."""
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/applications/{random_uuid}")
    assert response.status_code == 404
