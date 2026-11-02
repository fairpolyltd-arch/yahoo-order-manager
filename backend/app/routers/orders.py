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

import datetime
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models import Order, OrderItem, RawEmail, Attachment
from app.schemas import OrderResponse, OrderUpdate, DashboardMetrics, DailySummaryItem, CategorySummaryItem
from app.services.extractor import extract_full_order, detect_order_category

router = APIRouter(prefix="/orders", tags=["Orders"])

BN_DAYS = {
    "Monday": "সোমবার", "Tuesday": "মঙ্গলবার", "Wednesday": "বুধবার",
    "Thursday": "বৃহস্পতিবার", "Friday": "শুক্রবার", "Saturday": "শনিবার", "Sunday": "রবিবার"
}
BN_MONTHS = {
    1: "জানু", 2: "ফেব্রু", 3: "মার্চ", 4: "এপ্রিল", 5: "মে", 6: "জুন",
    7: "জুলাই", 8: "আগস্ট", 9: "সেপ্টে", 10: "অক্টো", 11: "নভে", 12: "ডিসে"
}

def get_effective_date(order: Order) -> datetime.date:
    """Determine effective date of an order based on Yahoo email received date or order date."""
    if order.raw_email and order.raw_email.date_received:
        return order.raw_email.date_received.date()
    if order.order_date:
        return order.order_date.date()
    if order.created_at:
        return order.created_at.date()
    return datetime.date.today()

@router.get("/daily-summary", response_model=List[DailySummaryItem])
def get_daily_summary(db: Session = Depends(get_db)):
    """Returns aggregated order counts & metrics for the past 7 days."""
    today = datetime.date.today()
    days_data = []

    # Pre-load all orders with their raw_email
    all_orders = db.query(Order).all()

    for i in range(7):
        target_date = today - datetime.timedelta(days=i)
        target_str = target_date.strftime("%Y-%m-%d")
        day_name = target_date.strftime("%A")
        day_num = target_date.day
        month_num = target_date.month

        # Filter orders for this date
        matching_orders = [o for o in all_orders if get_effective_date(o) == target_date]
        count = len(matching_orders)
        tot_qty = sum(o.total_quantity or 0.0 for o in matching_orders)
        tot_amt = sum(o.total_amount or 0.0 for o in matching_orders)

        if i == 0:
            label_en = f"Today ({target_date.strftime('%d %b')})"
            label_bn = f"আজকে ({day_num} {BN_MONTHS[month_num]})"
        elif i == 1:
            label_en = f"Yesterday ({target_date.strftime('%d %b')})"
            label_bn = f"গতকাল ({day_num} {BN_MONTHS[month_num]})"
        else:
            label_en = f"{target_date.strftime('%d %b')} ({day_name[:3]})"
            label_bn = f"{day_num} {BN_MONTHS[month_num]} ({BN_DAYS[day_name][:3]})"

        days_data.append(DailySummaryItem(
            date=target_str,
            day_name=day_name,
            label_en=label_en,
            label_bn=label_bn,
            order_count=count,
            total_quantity=round(tot_qty, 2),
            total_amount=round(tot_amt, 2),
            is_today=(i == 0)
        ))

    return days_data

@router.get("", response_model=List[OrderResponse])
def list_orders(
    search: Optional[str] = Query(None, description="Search in PO, Booking, Buyer"),
    status: Optional[str] = Query(None, description="CONFIRMED, REVIEW_NEEDED, DUPLICATE, CANCELLED"),
    category: Optional[str] = Query(None, description="Carton, Elastic, Poly, Jacquard Elastic, Other"),
    buyer: Optional[str] = Query(None, description="Filter by buyer"),
    day_filter: Optional[str] = Query(None, description="'today', 'yesterday', 'last_7_days', 'all', or 'YYYY-MM-DD'"),
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None,
    limit: int = 150,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Order)

    if status and status != "ALL":
        query = query.filter(Order.status == status)

    if category and category != "ALL":
        query = query.filter(Order.category.ilike(category))

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

    orders = query.order_by(Order.created_at.desc()).all()
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    seven_days_ago = today - datetime.timedelta(days=6)

    # Apply Day Filter
    if day_filter:
        day_filter = day_filter.strip().lower()
        if day_filter == "today":
            orders = [o for o in orders if get_effective_date(o) == today]
        elif day_filter == "yesterday":
            orders = [o for o in orders if get_effective_date(o) == yesterday]
        elif day_filter == "last_7_days":
            orders = [o for o in orders if get_effective_date(o) >= seven_days_ago]
        elif day_filter != "all":
            # Match exact date YYYY-MM-DD
            try:
                target_dt = datetime.datetime.strptime(day_filter, "%Y-%m-%d").date()
                orders = [o for o in orders if get_effective_date(o) == target_dt]
            except ValueError:
                pass

    if date_from:
        orders = [o for o in orders if get_effective_date(o) >= date_from]
    if date_to:
        orders = [o for o in orders if get_effective_date(o) <= date_to]

    return orders[offset:offset + limit]

@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    all_orders = db.query(Order).all()
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=6)

    total_orders = len(all_orders)
    confirmed_orders = sum(1 for o in all_orders if o.status == "CONFIRMED")
    review_needed = sum(1 for o in all_orders if o.status == "REVIEW_NEEDED")
    duplicate_orders = sum(1 for o in all_orders if o.status == "DUPLICATE")
    total_buyers = len(set(o.buyer_name for o in all_orders if o.buyer_name))
    total_quantity = sum(o.total_quantity or 0.0 for o in all_orders)

    # Today's metrics
    today_orders_list = [o for o in all_orders if get_effective_date(o) == today]
    today_orders = len(today_orders_list)
    today_quantity = sum(o.total_quantity or 0.0 for o in today_orders_list)

    # Past 7 days metrics
    past_7_days_orders = sum(1 for o in all_orders if get_effective_date(o) >= seven_days_ago)

    last_order = db.query(Order).order_by(Order.created_at.desc()).first()
    last_sync = last_order.created_at if last_order else None

    # Categories Summary
    CATEGORIES_META = [
        {"category": "Carton", "label_en": "Carton", "label_bn": "কার্টন", "icon": "fa-box"},
        {"category": "Elastic", "label_en": "Elastic", "label_bn": "ইলাস্টিক", "icon": "fa-ruler-combined"},
        {"category": "Poly", "label_en": "Poly", "label_bn": "পলি", "icon": "fa-bag-shopping"},
        {"category": "Jacquard Elastic", "label_en": "Jacquard Elastic", "label_bn": "জ্যাকর্ড ইলাস্টিক", "icon": "fa-certificate"},
        {"category": "Other", "label_en": "Other", "label_bn": "অন্যান্য", "icon": "fa-tags"},
    ]

    categories_summary = []
    for cat_def in CATEGORIES_META:
        c_name = cat_def["category"]
        matching = [o for o in all_orders if (o.category or "Other").lower() == c_name.lower()]
        categories_summary.append(CategorySummaryItem(
            category=c_name,
            label_en=cat_def["label_en"],
            label_bn=cat_def["label_bn"],
            icon=cat_def["icon"],
            order_count=len(matching),
            total_quantity=round(sum(o.total_quantity or 0.0 for o in matching), 2),
            total_amount=round(sum(o.total_amount or 0.0 for o in matching), 2)
        ))

    return DashboardMetrics(
        total_orders=total_orders,
        confirmed_orders=confirmed_orders,
        review_needed=review_needed,
        duplicate_orders=duplicate_orders,
        total_buyers=total_buyers,
        total_quantity=round(total_quantity, 2),
        today_orders=today_orders,
        today_quantity=round(today_quantity, 2),
        past_7_days_orders=past_7_days_orders,
        categories=categories_summary,
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
