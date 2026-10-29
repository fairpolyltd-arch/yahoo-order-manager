import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.database import Base, engine
from app.services.crypto import encrypt_value, decrypt_value

client = TestClient(app)

def setup_module():
    Base.metadata.create_all(bind=engine)

def test_crypto_service():
    secret = "yahoo_app_password_xyz123"
    encrypted = encrypt_value(secret)
    assert encrypted != secret, "Encrypted string should not equal plaintext"
    decrypted = decrypt_value(encrypted)
    assert decrypted == secret, f"Decryption failed: expected {secret}, got {decrypted}"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

def test_simulate_ingest_sample_order():
    # Primary sample test
    sample_subject = "Elastic booking for CCKL-01734/26& PO-2100011291 of VDE buyer"
    response = client.post(
        "/api/v1/orders/simulate-ingest",
        params={
            "subject": sample_subject,
            "sender": "purchase@vde-buyer.com",
            "body": "Urgent booking for elastic CCKL-01734/26. PO-2100011291. Qty: 15,000 PCS. Amount: $4,500."
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["booking_number"] == "CCKL-01734/26"
    assert data["po_number"] == "PO-2100011291"
    assert data["buyer_name"] == "VDE"
    assert data["order_type"] == "Elastic Booking"
    assert data["status"] == "CONFIRMED"
    assert data["confidence_score"] >= 0.8
    assert len(data["items"]) >= 1

def test_get_orders_and_metrics():
    # Metrics
    metrics_res = client.get("/api/v1/orders/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_orders"] >= 1
    assert metrics["confirmed_orders"] >= 1

    # Filtered search
    orders_res = client.get("/api/v1/orders?search=CCKL-01734")
    assert orders_res.status_code == 200
    orders = orders_res.json()
    assert len(orders) >= 1
    assert orders[0]["booking_number"] == "CCKL-01734/26"

def test_export_endpoints():
    excel_res = client.get("/api/v1/export/excel")
    assert excel_res.status_code == 200
    assert "spreadsheetml" in excel_res.headers.get("content-type", "")

    csv_res = client.get("/api/v1/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")

if __name__ == "__main__":
    test_crypto_service()
    test_root_endpoint()
    test_simulate_ingest_sample_order()
    test_get_orders_and_metrics()
    test_export_endpoints()
    print("ALL API TESTS PASSED SUCCESSFULLY!")
