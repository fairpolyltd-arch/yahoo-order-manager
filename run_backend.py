import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

import uvicorn

if __name__ == "__main__":
    print("==================================================================")
    print("  Starting Yahoo Mail Order Extraction & Management Backend Server")
    print("  Web Dashboard: http://localhost:8000")
    print("  OpenAPI Docs:  http://localhost:8000/docs")
    print("==================================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

