import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import engine, Base
from app.routers import accounts, orders, sync, export
from app.services.sync_service import sync_manager

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready Yahoo Mail Order Extraction and Management System"
)

# Enable CORS for Web Dashboard and Android Client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(accounts.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(sync.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)

@app.get("/api/v1/system/network-info")
def get_network_info():
    ips = []
    try:
        hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            ips.append(primary_ip)
        except Exception:
            primary_ip = "127.0.0.1"
        finally:
            s.close()

        addr_info = socket.getaddrinfo(hostname, None)
        for item in addr_info:
            ip = item[4][0]
            if ":" not in ip and ip != "127.0.0.1" and ip not in ips:
                ips.append(ip)
    except Exception:
        primary_ip = "127.0.0.1"
        ips = ["127.0.0.1"]

    return {
        "hostname": socket.gethostname(),
        "primary_ip": primary_ip,
        "all_ips": ips,
        "port": 8000,
        "network_url": f"http://{primary_ip}:8000",
        "local_url": "http://localhost:8000"
    }

# Serve Web Dashboard Static Files
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def start_keep_alive():
    import threading
    import time
    import requests
    def _ping():
        time.sleep(60) # Wait 1 min after startup
        while True:
            try:
                requests.get("https://yahoo-order-manager.onrender.com/api/v1/system/network-info", timeout=20)
            except Exception:
                pass
            time.sleep(600) # Every 10 mins
    t = threading.Thread(target=_ping, daemon=True)
    t.start()

@app.on_event("startup")
def startup_event():
    print("[INIT] Starting Yahoo Mail Background Synchronization Engine...")
    sync_manager.start()
    start_keep_alive()

@app.on_event("shutdown")
def shutdown_event():
    print("[SHUTDOWN] Stopping Yahoo Mail Background Synchronization Engine...")
    sync_manager.stop()

@app.get("/")
def root():
    from fastapi.responses import FileResponse
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
