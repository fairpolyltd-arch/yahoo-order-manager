from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import MailAccount, SyncLog
from app.schemas import SyncTriggerRequest, SyncLogResponse
from app.services.sync_service import run_sync_for_account

router = APIRouter(prefix="/sync", tags=["Email Synchronization"])

@router.post("/trigger")
def trigger_sync(payload: SyncTriggerRequest, db: Session = Depends(get_db)):
    accounts = []
    if payload.account_id:
        acc = db.query(MailAccount).filter(MailAccount.id == payload.account_id).first()
        if not acc:
            raise HTTPException(status_code=404, detail="Mail account not found")
        accounts.append(acc)
    else:
        accounts = db.query(MailAccount).all()

    if not accounts:
        raise HTTPException(
            status_code=400,
            detail="No Yahoo Mail account configured. Please add an account in settings first."
        )

    results = []
    for acc in accounts:
        res = run_sync_for_account(
            db=db,
            account_id=acc.id,
            max_emails=payload.max_emails,
            force_all=payload.force_all
        )
        results.append({"account": acc.email, "result": res})

    return {"success": True, "results": results}

@router.get("/logs", response_model=List[SyncLogResponse])
def get_sync_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit).all()
