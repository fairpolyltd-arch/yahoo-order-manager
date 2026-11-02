import os
import io
import datetime
from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Order, OrderItem
from app.config import EXPORTS_DIR

def generate_orders_dataframe(db: Session, status: Optional[str] = None, buyer: Optional[str] = None, category: Optional[str] = None) -> pd.DataFrame:
    query = db.query(Order)
    if status and status != "ALL":
        query = query.filter(Order.status == status)
    if category and category != "ALL":
        query = query.filter(Order.category.ilike(category))
    if buyer:
        query = query.filter(Order.buyer_name.ilike(f"%{buyer}%"))
    
    orders = query.order_by(Order.created_at.desc()).all()

    records = []
    for ord in orders:
        items_summary = "; ".join([
            f"{it.item_code or 'Item'}: {it.quantity} {it.unit} @ {ord.currency} {it.unit_price}"
            for it in ord.items
        ])
        records.append({
            "Order ID": ord.id,
            "PO Number": ord.po_number or "N/A",
            "Booking Number": ord.booking_number or "N/A",
            "Buyer": ord.buyer_name or "Unknown",
            "Category": ord.category or "Other",
            "Order Type": ord.order_type or "N/A",
            "Order Date": ord.order_date.strftime("%Y-%m-%d") if ord.order_date else "N/A",
            "Delivery Date": ord.delivery_date.strftime("%Y-%m-%d") if ord.delivery_date else "N/A",
            "Total Quantity": ord.total_quantity,
            "Unit": ord.quantity_unit,
            "Currency": ord.currency,
            "Total Amount": ord.total_amount,
            "Confidence": f"{int((ord.confidence_score or 0) * 100)}%",
            "Status": ord.status,
            "Items Breakdown": items_summary,
            "Source Email Subject": ord.raw_email.subject if ord.raw_email else "Manual",
            "Created At": ord.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return pd.DataFrame(records)

def export_orders_to_excel(db: Session, status: Optional[str] = None, buyer: Optional[str] = None, category: Optional[str] = None) -> str:
    df = generate_orders_dataframe(db, status=status, buyer=buyer, category=category)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"orders_export_{timestamp}.xlsx"
    filepath = EXPORTS_DIR / filename

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Orders", index=False)
        # Auto-adjust column width
        worksheet = writer.sheets["Orders"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    return str(filepath)

def export_orders_to_csv(db: Session, status: Optional[str] = None, buyer: Optional[str] = None, category: Optional[str] = None) -> str:
    df = generate_orders_dataframe(db, status=status, buyer=buyer, category=category)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"orders_export_{timestamp}.csv"
    filepath = EXPORTS_DIR / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return str(filepath)
