import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

class MailAccount(Base):
    __tablename__ = "mail_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    auth_type = Column(String(50), default="app_password")  # app_password | oauth2
    encrypted_secret = Column(Text, nullable=False)
    imap_server = Column(String(255), default="imap.mail.yahoo.com")
    imap_port = Column(Integer, default=993)
    folder_name = Column(String(100), default="INBOX")
    last_sync_uid = Column(Integer, default=0)
    last_sync_time = Column(DateTime, nullable=True)
    sync_interval_minutes = Column(Integer, default=15)
    auto_sync_enabled = Column(Boolean, default=True)
    status = Column(String(50), default="disconnected")  # connected | disconnected | error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    emails = relationship("RawEmail", back_populates="account", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="account", cascade="all, delete-orphan")


class RawEmail(Base):
    __tablename__ = "raw_emails"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("mail_accounts.id"), nullable=True)
    message_id = Column(String(500), unique=True, index=True, nullable=False)
    uid = Column(Integer, index=True, nullable=True)
    sender = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    subject = Column(String(1000), nullable=True)
    date_received = Column(DateTime, nullable=True)
    body_plain = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    has_attachments = Column(Boolean, default=False)
    is_order_candidate = Column(Boolean, default=False)
    sync_status = Column(String(50), default="pending")  # pending | processed | skipped | failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    account = relationship("MailAccount", back_populates="emails")
    orders = relationship("Order", back_populates="raw_email")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("raw_emails.id"), nullable=True)
    
    # Core Extraction Fields
    po_number = Column(String(100), index=True, nullable=True)
    booking_number = Column(String(100), index=True, nullable=True)
    buyer_name = Column(String(150), index=True, nullable=True)
    order_type = Column(String(100), nullable=True)  # e.g., "Elastic Booking", "Purchase Order", etc.
    category = Column(String(50), index=True, default="Other")  # Carton | Elastic | Poly | Jacquard Elastic | Other
    
    order_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    total_quantity = Column(Float, default=0.0)
    quantity_unit = Column(String(20), default="PCS")
    currency = Column(String(10), default="USD")
    total_amount = Column(Float, default=0.0)
    
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    status = Column(String(50), default="CONFIRMED")  # CONFIRMED | REVIEW_NEEDED | DUPLICATE | CANCELLED
    notes = Column(Text, nullable=True)
    
    # Duplicate detection & deduplication references
    duplicate_of_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    raw_fingerprint = Column(String(64), index=True, nullable=True)  # SHA-256
    source = Column(String(50), default="subject_body")  # subject_body | attachment | manual
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    raw_email = relationship("RawEmail", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="order")
    duplicate_orders = relationship("Order", backref="original_order", remote_side=[id])


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)
    color = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String(20), default="PCS")
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)

    order = relationship("Order", back_populates="items")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("raw_emails.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, xlsx, docx, csv, etc.
    file_size = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    extraction_status = Column(String(50), default="pending")  # success | failed | skipped
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    email = relationship("RawEmail", back_populates="attachments")
    order = relationship("Order", back_populates="attachments")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("mail_accounts.id"), nullable=True)
    status = Column(String(50), default="started")  # started | completed | failed
    emails_fetched = Column(Integer, default=0)
    orders_extracted = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    account = relationship("MailAccount", back_populates="sync_logs")
