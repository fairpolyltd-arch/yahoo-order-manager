import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("==================================================================")
    print("  Starting Yahoo Mail Order Extraction & Management Backend Server")
    print(f"  Port: {port}")
    print(f"  Web Dashboard: http://localhost:{port}")
    print(f"  OpenAPI Docs:  http://localhost:{port}/docs")
    print("==================================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

