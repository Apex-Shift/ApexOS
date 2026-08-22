"""Simple launcher for ApexOS — run from the project root."""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    print("=========================================================")
    print("      APEXOS  —  Desktop Edition v2.2.0                  ")
    print("=========================================================")
    print("  → http://127.0.0.1:8000")
    print("=========================================================")
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=True)
