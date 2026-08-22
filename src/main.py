import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

def main():
    print("=========================================================")
    print("      APEXOS  —  Desktop Edition v2.2.0                  ")
    print("=========================================================")
    print("  → http://127.0.0.1:8000")
    print("=========================================================")
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
