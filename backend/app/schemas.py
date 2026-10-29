import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Order Item Schemas
class OrderItemBase(BaseModel):
    item_code: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: float = 0.0
    unit: str = "PCS"
    unit_price: float = 0.0
    total_price: float = 0.0

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    class Config:
        from_attributes = True


# Attachment Schemas
class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    extraction_status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Order Schemas
class OrderBase(BaseModel):
    po_number: Optional[str] = None
    booking_number: Optional[str] = None
    buyer_name: Optional[str] = None
    order_type: Optional[str] = None
    order_date: Optional[datetime.datetime] = None
    delivery_date: Optional[datetime.datetime] = None
    total_quantity: float = 0.0
    quantity_unit: str = "PCS"
    currency: str = "USD"
    total_amount: float = 0.0
    status: str = "CONFIRMED"
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    email_id: Optional[int] = None
    items: List[OrderItemCreate] = []

class OrderUpdate(BaseModel):
    po_number: Optional[str] = None
    booking_number: Optional[str] = None
    buyer_name: Optional[str] = None
    order_type: Optional[str] = None
    order_date: Optional[datetime.datetime] = None
    delivery_date: Optional[datetime.datetime] = None
    total_quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class RawEmailSummary(BaseModel):
    id: int
    message_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    date_received: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    id: int
    email_id: Optional[int] = None
    confidence_score: float
    duplicate_of_id: Optional[int] = None
    source: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: List[OrderItemResponse] = []
    attachments: List[AttachmentResponse] = []
    raw_email: Optional[RawEmailSummary] = None

    class Config:
        from_attributes = True


# Mail Account Schemas
class MailAccountSetup(BaseModel):
    email: str
    auth_type: str = "app_password"  # app_password | oauth2
    password_or_token: str
    imap_server: str = "imap.mail.yahoo.com"
    imap_port: int = 993
    folder_name: str = "INBOX"
    sync_interval_minutes: int = 15
    auto_sync_enabled: bool = True

class MailAccountResponse(BaseModel):
    id: int
    email: str
    auth_type: str
    imap_server: str
    imap_port: int
    folder_name: str
    last_sync_uid: int
    last_sync_time: Optional[datetime.datetime] = None
    sync_interval_minutes: int
    auto_sync_enabled: bool
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# Sync Schemas
class SyncTriggerRequest(BaseModel):
    account_id: Optional[int] = None
    max_emails: int = 50
    force_all: bool = False

class SyncLogResponse(BaseModel):
    id: int
    account_id: Optional[int] = None
    status: str
    emails_fetched: int
    orders_extracted: int
    error_message: Optional[str] = None
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# Dashboard KPI Metrics
class DashboardMetrics(BaseModel):
    total_orders: int
    confirmed_orders: int
    review_needed: int
    duplicate_orders: int
    total_buyers: int
    total_quantity: float
    last_sync_time: Optional[datetime.datetime] = None
    sync_status: str
