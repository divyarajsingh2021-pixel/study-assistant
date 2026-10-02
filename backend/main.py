import os
import sys
from pathlib import Path

# Ensure backend dir is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting DSC Backend on http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port)
