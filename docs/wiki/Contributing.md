# Contributing

## Development setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Adding a shell command

1. Map the command name in `src/api/server.py` (WebSocket handler)  
2. Implement logic in `ApexKernel.syscall` if it needs VFS/session state  
3. Document it in [Terminal & Shell](Terminal-and-Shell)  

## Adding a built-in desktop app

1. Register the app in `APP_REGISTRY` inside `server.py`  
2. Implement `openMyApp()` and wire it in `openApp()`  
3. Optionally add `apps/<id>/manifest.json`  

## Adding an `.apx` package

1. Create a folder with `manifest.json` and UI entry  
2. Zip it as `something.apx`  
3. Place samples under `packages/`  

## Code style

- Python: readable, minimal dependencies  
- JS: no build step required (vanilla)  
- User-facing strings: **English**  

## Pull requests

- Keep changes focused  
- Update wiki pages when behavior changes  
- Do not commit `venv/`, `__pycache__/`, or secrets  
