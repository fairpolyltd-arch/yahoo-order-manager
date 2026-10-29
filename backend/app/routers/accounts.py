from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import MailAccount
from app.schemas import MailAccountSetup, MailAccountResponse
from app.services.crypto import encrypt_value, decrypt_value
from app.services.imap_client import test_yahoo_connection

router = APIRouter(prefix="/accounts", tags=["Mail Accounts"])

@router.get("", response_model=List[MailAccountResponse])
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(MailAccount).all()
    return accounts

@router.post("/setup", response_model=MailAccountResponse)
def setup_account(payload: MailAccountSetup, db: Session = Depends(get_db)):
    # Test connection first
    test_res = test_yahoo_connection(
        email_address=payload.email,
        secret=payload.password_or_token,
        auth_type=payload.auth_type,
        server=payload.imap_server,
        port=payload.imap_port
    )

    encrypted_sec = encrypt_value(payload.password_or_token)

    account = db.query(MailAccount).filter(MailAccount.email == payload.email).first()
    if not account:
        account = MailAccount(
            email=payload.email,
            auth_type=payload.auth_type,
            encrypted_secret=encrypted_sec,
            imap_server=payload.imap_server,
            imap_port=payload.imap_port,
            folder_name=payload.folder_name,
            sync_interval_minutes=payload.sync_interval_minutes,
            auto_sync_enabled=payload.auto_sync_enabled,
            status="connected" if test_res["success"] else "error",
            error_message=None if test_res["success"] else test_res["message"]
        )
        db.add(account)
    else:
        account.auth_type = payload.auth_type
        account.encrypted_secret = encrypted_sec
        account.imap_server = payload.imap_server
        account.imap_port = payload.imap_port
        account.folder_name = payload.folder_name
        account.sync_interval_minutes = payload.sync_interval_minutes
        account.auto_sync_enabled = payload.auto_sync_enabled
        account.status = "connected" if test_res["success"] else "error"
        account.error_message = None if test_res["success"] else test_res["message"]

    db.commit()
    db.refresh(account)
    return account

@router.post("/test-connection")
def test_connection_endpoint(payload: MailAccountSetup):
    res = test_yahoo_connection(
        email_address=payload.email,
        secret=payload.password_or_token,
        auth_type=payload.auth_type,
        server=payload.imap_server,
        port=payload.imap_port
    )
    return res
