import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
EXPORTS_DIR = DATA_DIR / "exports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "Yahoo Mail Order Management & Extraction System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'orders.db'}")
    
    # Security: AES encryption secret key for storing Yahoo passwords/tokens securely
    SECRET_KEY: str = os.getenv("SECRET_KEY", "y@h00-0rd3r-m@n@g3m3nt-s3cr3t-k3y-2026-s3cur3!")
    
    # Yahoo Mail Defaults
    YAHOO_IMAP_SERVER: str = "imap.mail.yahoo.com"
    YAHOO_IMAP_PORT: int = 993
    DEFAULT_SYNC_INTERVAL_MINUTES: int = 15

settings = Settings()
