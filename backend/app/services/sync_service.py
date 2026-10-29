import datetime
import threading
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings, ATTACHMENTS_DIR
from app.database import SessionLocal
from app.models import MailAccount, RawEmail, Order, OrderItem, Attachment, SyncLog
from app.services.crypto import decrypt_value
from app.services.imap_client import YahooIMAPClient
from app.services.attachment_service import process_attachment
from app.services.extractor import is_order_email, extract_full_order, parse_date_string

def run_sync_for_account(db: Session, account_id: int, max_emails: int = 50, force_all: bool = False) -> Dict[str, Any]:
    """Execute synchronous incremental sync for a given Yahoo Mail account."""
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        return {"success": False, "error": "Account not found"}

    secret = decrypt_value(account.encrypted_secret)
    if not secret:
        return {"success": False, "error": "Unable to decrypt account credentials"}

    sync_log = SyncLog(
        account_id=account.id,
        status="started",
        emails_fetched=0,
        orders_extracted=0,
        started_at=datetime.datetime.utcnow()
    )
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    client = YahooIMAPClient(
        email_address=account.email,
        secret=secret,
        auth_type=account.auth_type,
        server=account.imap_server,
        port=account.imap_port
    )

    ok, msg = client.connect()
    if not ok:
        sync_log.status = "failed"
        sync_log.error_message = msg
        sync_log.completed_at = datetime.datetime.utcnow()
        account.status = "error"
        account.error_message = msg
        db.commit()
        return {"success": False, "error": msg}

    account.status = "connected"
    account.error_message = None
    db.commit()

    last_uid = 0 if force_all else (account.last_sync_uid or 0)
    highest_uid = last_uid
    emails_count = 0
    orders_count = 0

    try:
        email_dicts = client.fetch_new_emails(
            folder=account.folder_name,
            last_uid=last_uid,
            max_results=max_emails,
            save_attachments_dir=ATTACHMENTS_DIR
        )

        for ed in email_dicts:
            uid = ed.get("uid", 0)
            if uid > highest_uid:
                highest_uid = uid

            # Check if email already ingested
            existing_email = db.query(RawEmail).filter(RawEmail.message_id == ed["message_id"]).first()
            if existing_email:
                continue

            emails_count += 1
            date_received = parse_date_string(ed.get("date_str", "")) or datetime.datetime.utcnow()
            is_order = is_order_email(ed["subject"], ed["body_plain"])

            raw_email = RawEmail(
                account_id=account.id,
                message_id=ed["message_id"],
                uid=uid,
                sender=ed.get("sender"),
                recipient=ed.get("recipient"),
                subject=ed.get("subject"),
                date_received=date_received,
                body_plain=ed.get("body_plain"),
                body_html=ed.get("body_html"),
                has_attachments=bool(ed.get("attachments")),
                is_order_candidate=is_order,
                sync_status="pending"
            )
            db.add(raw_email)
            db.flush()

            # Process attachments
            att_processed_data = []
            saved_attachments = []
            for att_info in ed.get("attachments", []):
                extracted = process_attachment(att_info["file_path"])
                att_processed_data.append({
                    "file_name": att_info["file_name"],
                    "text": extracted.get("text", ""),
                    "items": extracted.get("items", [])
                })
                att_record = Attachment(
                    email_id=raw_email.id,
                    file_name=att_info["file_name"],
                    file_path=att_info["file_path"],
                    file_type=att_info["file_type"],
                    file_size=att_info["file_size"],
                    extracted_text=extracted.get("text", "")[:4000],
                    extraction_status="success" if extracted.get("text") else "skipped"
                )
                db.add(att_record)
                saved_attachments.append(att_record)

            db.flush()

            # If it's an order candidate or has order attachments, extract order
            if is_order:
                extracted_data = extract_full_order(
                    subject=ed["subject"],
                    body_plain=ed.get("body_plain", ""),
                    body_html=ed.get("body_html", ""),
                    attachment_data=att_processed_data
                )

                # Duplicate detection by fingerprint or PO number + Buyer
                fingerprint = extracted_data["fingerprint"]
                existing_order = None
                if extracted_data.get("po_number") and extracted_data.get("buyer_name"):
                    existing_order = db.query(Order).filter(
                        Order.po_number == extracted_data["po_number"],
                        Order.buyer_name == extracted_data["buyer_name"]
                    ).first()
                if not existing_order and fingerprint:
                    existing_order = db.query(Order).filter(Order.raw_fingerprint == fingerprint).first()

                order_status = extracted_data["status"]
                duplicate_of_id = None
                if existing_order:
                    order_status = "DUPLICATE"
                    duplicate_of_id = existing_order.id

                new_order = Order(
                    email_id=raw_email.id,
                    po_number=extracted_data.get("po_number"),
                    booking_number=extracted_data.get("booking_number"),
                    buyer_name=extracted_data.get("buyer_name"),
                    order_type=extracted_data.get("order_type"),
                    order_date=extracted_data.get("order_date") or date_received,
                    delivery_date=extracted_data.get("delivery_date"),
                    total_quantity=extracted_data.get("total_quantity", 0.0),
                    quantity_unit=extracted_data.get("quantity_unit", "PCS"),
                    currency=extracted_data.get("currency", "USD"),
                    total_amount=extracted_data.get("total_amount", 0.0),
                    confidence_score=extracted_data.get("confidence_score", 0.0),
                    status=order_status,
                    duplicate_of_id=duplicate_of_id,
                    raw_fingerprint=fingerprint,
                    source="subject_body"
                )
                db.add(new_order)
                db.flush()

                # Link attachments to order
                for att_rec in saved_attachments:
                    att_rec.order_id = new_order.id

                # Add order items
                for item in extracted_data.get("items", []):
                    order_item = OrderItem(
                        order_id=new_order.id,
                        item_code=item.get("item_code"),
                        description=item.get("description"),
                        color=item.get("color"),
                        size=item.get("size"),
                        quantity=item.get("quantity", 0.0),
                        unit=item.get("unit", "PCS"),
                        unit_price=item.get("unit_price", 0.0),
                        total_price=item.get("total_price", 0.0)
                    )
                    db.add(order_item)

                raw_email.sync_status = "processed"
                orders_count += 1
            else:
                raw_email.sync_status = "skipped"

        # Update Account and Log
        account.last_sync_uid = highest_uid
        account.last_sync_time = datetime.datetime.utcnow()
        account.status = "connected"

        sync_log.status = "completed"
        sync_log.emails_fetched = emails_count
        sync_log.orders_extracted = orders_count
        sync_log.completed_at = datetime.datetime.utcnow()

        db.commit()
    except Exception as e:
        db.rollback()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        sync_log.completed_at = datetime.datetime.utcnow()
        db.commit()
        return {"success": False, "error": str(e)}
    finally:
        client.disconnect()

    return {
        "success": True,
        "emails_fetched": emails_count,
        "orders_extracted": orders_count,
        "highest_uid": highest_uid
    }


# Background Sync Scheduler Thread
class BackgroundSyncManager:
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _worker_loop(self):
        while self.running:
            try:
                db = SessionLocal()
                accounts = db.query(MailAccount).filter(MailAccount.auto_sync_enabled == True).all()
                now = datetime.datetime.utcnow()
                for acc in accounts:
                    interval_sec = (acc.sync_interval_minutes or 15) * 60
                    last_time = acc.last_sync_time or datetime.datetime.min
                    if (now - last_time).total_seconds() >= interval_sec:
                        run_sync_for_account(db, acc.id)
                db.close()
            except Exception as e:
                print(f"Background sync manager loop error: {e}")

            # Sleep 60 seconds before next check
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1)

sync_manager = BackgroundSyncManager()
