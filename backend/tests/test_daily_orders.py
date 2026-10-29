import sys
from pathlib import Path

# Force UTF-8 stdout for Bengali text
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def test_daily_features():
    with TestClient(app) as client:
        # 1. Test Daily Summary Endpoint
        res = client.get("/api/v1/orders/daily-summary")
        assert res.status_code == 200, res.text
        summary = res.json()
        print("\n--- PAST 7 DAYS SUMMARY ---")
        assert len(summary) == 7, f"Expected 7 days, got {len(summary)}"
        for item in summary:
            print(f"[{item['date']}] {item['label_en']} / {item['label_bn']} -> Orders: {item['order_count']}, Total Qty: {item['total_quantity']}")

        # 2. Test Today's Orders Filter
        res_today = client.get("/api/v1/orders?day_filter=today")
        assert res_today.status_code == 200
        today_orders = res_today.json()
        print(f"\nOrders for TODAY: {len(today_orders)}")
        for o in today_orders:
            print(f"  - PO: {o['po_number']} | Booking: {o['booking_number']} | Buyer: {o['buyer_name']} | Qty: {o['total_quantity']}")

        # 3. Test Yesterday's Orders Filter
        res_yesterday = client.get("/api/v1/orders?day_filter=yesterday")
        assert res_yesterday.status_code == 200
        yesterday_orders = res_yesterday.json()
        print(f"\nOrders for YESTERDAY: {len(yesterday_orders)}")

        # 4. Test Metrics Endpoint with new today and 7-day counts
        metrics_res = client.get("/api/v1/orders/metrics")
        assert metrics_res.status_code == 200
        metrics = metrics_res.json()
        print("\n--- UPDATED METRICS ---")
        print(f"Total Orders: {metrics['total_orders']}")
        print(f"Today Orders: {metrics['today_orders']}")
        print(f"Today Quantity: {metrics['today_quantity']}")
        print(f"Past 7 Days Orders: {metrics['past_7_days_orders']}")

if __name__ == "__main__":
    test_daily_features()
    print("\nALL DAILY ORDER TESTS PASSED!")
