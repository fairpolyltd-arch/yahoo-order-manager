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

# Serve Web Dashboard Static Files
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.on_event("startup")
def startup_event():
    print("[INIT] Starting Yahoo Mail Background Synchronization Engine...")
    sync_manager.start()

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
