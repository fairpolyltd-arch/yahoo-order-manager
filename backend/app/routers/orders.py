import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models import Order, OrderItem, RawEmail, Attachment
from app.schemas import OrderResponse, OrderUpdate, DashboardMetrics
from app.services.extractor import extract_full_order

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("", response_model=List[OrderResponse])
def list_orders(
    search: Optional[str] = Query(None, description="Search in PO, Booking, Buyer"),
    status: Optional[str] = Query(None, description="CONFIRMED, REVIEW_NEEDED, DUPLICATE, CANCELLED"),
    buyer: Optional[str] = Query(None, description="Filter by buyer"),
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Order)

    if status and status != "ALL":
        query = query.filter(Order.status == status)

    if buyer:
        query = query.filter(Order.buyer_name.ilike(f"%{buyer}%"))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Order.po_number.ilike(search_pattern),
                Order.booking_number.ilike(search_pattern),
                Order.buyer_name.ilike(search_pattern),
                Order.order_type.ilike(search_pattern)
            )
        )

    if date_from:
        query = query.filter(Order.created_at >= datetime.datetime.combine(date_from, datetime.time.min))
    if date_to:
        query = query.filter(Order.created_at <= datetime.datetime.combine(date_to, datetime.time.max))

    return query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    confirmed_orders = db.query(func.count(Order.id)).filter(Order.status == "CONFIRMED").scalar() or 0
    review_needed = db.query(func.count(Order.id)).filter(Order.status == "REVIEW_NEEDED").scalar() or 0
    duplicate_orders = db.query(func.count(Order.id)).filter(Order.status == "DUPLICATE").scalar() or 0
    total_buyers = db.query(func.count(func.distinct(Order.buyer_name))).scalar() or 0
    total_quantity = db.query(func.sum(Order.total_quantity)).scalar() or 0.0

    last_order = db.query(Order).order_by(Order.created_at.desc()).first()
    last_sync = last_order.created_at if last_order else None

    return DashboardMetrics(
        total_orders=total_orders,
        confirmed_orders=confirmed_orders,
        review_needed=review_needed,
        duplicate_orders=duplicate_orders,
        total_buyers=total_buyers,
        total_quantity=round(total_quantity, 2),
        last_sync_time=last_sync,
        sync_status="active"
    )

@router.get("/{order_id}", response_model=OrderResponse)
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(order, field, val)

    order.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return {"success": True, "message": f"Order #{order_id} deleted successfully"}

# Endpoint to test or ingest simulated / direct order emails for QA verification
@router.post("/simulate-ingest", response_model=OrderResponse)
def simulate_order_ingest(
    subject: str = "Elastic booking for CCKL-01734/26& PO-2100011291 of VDE buyer",
    sender: str = "order.desk@vde-apparel.com",
    body: str = "Please process the urgent booking for elastic. Delivery required by 2026-11-20. Total Qty: 15,000 PCS. Value: $4,500.",
    db: Session = Depends(get_db)
):
    msg_id = f"sim-{uuid.uuid4().hex[:12]}@yahoo.com"
    raw_email = RawEmail(
        message_id=msg_id,
        sender=sender,
        subject=subject,
        date_received=datetime.datetime.utcnow(),
        body_plain=body,
        body_html=f"<p>{body}</p>",
        has_attachments=False,
        is_order_candidate=True,
        sync_status="processed"
    )
    db.add(raw_email)
    db.flush()

    extracted = extract_full_order(subject=subject, body_plain=body, body_html="")

    new_order = Order(
        email_id=raw_email.id,
        po_number=extracted.get("po_number"),
        booking_number=extracted.get("booking_number"),
        buyer_name=extracted.get("buyer_name"),
        order_type=extracted.get("order_type"),
        order_date=extracted.get("order_date") or datetime.datetime.utcnow(),
        delivery_date=extracted.get("delivery_date"),
        total_quantity=extracted.get("total_quantity") or 15000.0,
        quantity_unit=extracted.get("quantity_unit") or "PCS",
        currency=extracted.get("currency") or "USD",
        total_amount=extracted.get("total_amount") or 4500.0,
        confidence_score=extracted.get("confidence_score") or 1.0,
        status="CONFIRMED",
        raw_fingerprint=extracted.get("fingerprint"),
        source="subject_body"
    )
    db.add(new_order)
    db.flush()

    # Add sample line items
    sample_item1 = OrderItem(
        order_id=new_order.id,
        item_code="EL-VDE-40",
        description="Jacquard Elastic 40mm - Navy/White",
        color="Navy",
        size="40mm",
        quantity=10000.0,
        unit="PCS",
        unit_price=0.30,
        total_price=3000.0
    )
    sample_item2 = OrderItem(
        order_id=new_order.id,
        item_code="EL-VDE-25",
        description="Woven Elastic 25mm - White",
        color="White",
        size="25mm",
        quantity=5000.0,
        unit="PCS",
        unit_price=0.30,
        total_price=1500.0
    )
    db.add_all([sample_item1, sample_item2])

    db.commit()
    db.refresh(new_order)
    return new_order
