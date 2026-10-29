import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.extractor import extract_subject_details, extract_full_order

def test_primary_sample():
    subject = "Elastic booking for CCKL-01734/26& PO-2100011291 of VDE buyer"
    res = extract_subject_details(subject)
    print("Test Primary Sample Result:", res)
    assert res["booking_number"] == "CCKL-01734/26", f"Expected CCKL-01734/26, got {res['booking_number']}"
    assert res["po_number"] == "PO-2100011291", f"Expected PO-2100011291, got {res['po_number']}"
    assert res["buyer_name"] == "VDE", f"Expected VDE, got {res['buyer_name']}"
    assert res["order_type"] == "Elastic Booking", f"Expected Elastic Booking, got {res['order_type']}"
    print("[PASS] Primary sample test passed successfully!")

def test_additional_patterns():
    # Variant 1: Fabric booking with buyer upfront
    sub1 = "Fabric Booking: BK-9942/2026 for H&M Buyer - PO# 45009123"
    res1 = extract_subject_details(sub1)
    print("Variant 1 Result:", res1)
    assert res1["order_type"] == "Fabric Booking"
    assert "45009123" in (res1["po_number"] or "")

    # Variant 2: Standard PO
    sub2 = "Purchase Order PO-7822910 of TARGET buyer"
    res2 = extract_subject_details(sub2)
    print("Variant 2 Result:", res2)
    assert res2["buyer_name"] == "TARGET"
    assert res2["po_number"] == "PO-7822910"

    # Variant 3: Full order extraction with body and HTML items
    html_body = """
    <html>
      <body>
        <p>Dear Team, please process the booking below:</p>
        <p>Delivery Date: 2026-11-15</p>
        <table border="1">
          <tr><th>Item Code</th><th>Description</th><th>Color</th><th>Qty</th><th>Price</th></tr>
          <tr><td>EL-01</td><td>Jacquard Elastic 40mm</td><td>Black</td><td>5,000</td><td>$0.45</td></tr>
          <tr><td>EL-02</td><td>Woven Elastic 25mm</td><td>White</td><td>2,500</td><td>$0.30</td></tr>
        </table>
      </body>
    </html>
    """
    order = extract_full_order(
        subject="Elastic booking for CCKL-01734/26& PO-2100011291 of VDE buyer",
        body_plain="Please see attached booking sheet.",
        body_html=html_body
    )
    print("Full Order Result:", order)
    assert order["booking_number"] == "CCKL-01734/26"
    assert order["po_number"] == "PO-2100011291"
    assert order["buyer_name"] == "VDE"
    assert len(order["items"]) == 2
    assert order["total_quantity"] == 7500.0
    assert order["confidence_score"] >= 0.8
    assert order["status"] == "CONFIRMED"
    print("[PASS] Full order extraction test passed successfully!")

if __name__ == "__main__":
    test_primary_sample()
    test_additional_patterns()
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
