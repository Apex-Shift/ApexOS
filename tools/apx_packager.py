#!/usr/bin/env python3
"""Pack a folder into an ApexOS .apx (zip + manifest)."""
import argparse, json, zipfile
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="ApexOS .apx packager")
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument("--perms", nargs="*", default=[])
    args = ap.parse_args()
    src = Path(args.src)
    manifest = {
        "name": args.name,
        "id": args.id,
        "version": args.version,
        "permissions": args.perms,
        "entry": "index.html" if (src / "index.html").exists() else "index.js",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        for f in src.rglob("*"):
            if f.is_file() and f.name != "manifest.json":
                zf.write(f, f.relative_to(src).as_posix())
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
