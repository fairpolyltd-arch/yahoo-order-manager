import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Attachment
from app.services.export_service import export_orders_to_excel, export_orders_to_csv

router = APIRouter(tags=["Export & Attachments"])

@router.get("/export/excel")
def download_excel(
    status: Optional[str] = Query(None),
    buyer: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        filepath = export_orders_to_excel(db, status=status, buyer=buyer)
        filename = os.path.basename(filepath)
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel export: {str(e)}")

@router.get("/export/csv")
def download_csv(
    status: Optional[str] = Query(None),
    buyer: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        filepath = export_orders_to_csv(db, status=status, buyer=buyer)
        filename = os.path.basename(filepath)
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV export: {str(e)}")

@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, db: Session = Depends(get_db)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not att or not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="Attachment file not found")

    return FileResponse(
        path=att.file_path,
        filename=att.file_name,
        media_type="application/octet-stream"
    )
