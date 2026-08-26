# ApexOS Hybrid Edition
<img width="1366" height="610" alt="image" src="https://github.com/user-attachments/assets/0b687715-243d-41ce-a929-0717e11c6b60" />

Virtual operating system in the browser — **decoupled core** + **HexaDE** desktop environment.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)

## Architecture

```text
static/                 ← Desktop Environment (HexaDE)
  css/hexade.css
  js/apex-host.js       ← WebSocket / session bridge
  js/hexade-de.js       ← Deskbar, windows, apps, context menu
  index.html

src/                    ← OS core (no UI chrome)
  api/server.py         ← REST + WebSocket only
  core/                 ← kernel, scheduler, sudo
  filesystem/           ← VFS
  auth/                 ← login
```

Swap or fork the DE under `static/` without touching the kernel.

## Quick start

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8000**

| User  | Password |
|-------|----------|
| root  | password |
| guest | guest    |

## Features

- **HexaDE Deskbar** (top): app menu, window list, calendar, USB/BT when available, logoff  
- **Context menu** on desktop and icons  
- **Terminal** with `sudo` (15 min elevation, red titlebar)  
- **Task Manager** with privilege gates  
- **`.apx` packages** + permission gatekeeper  
- **Web APIs**: network status, WebUSB, Web Bluetooth  
- **Wasm Test**: validates `WebAssembly.instantiate` with a minimal module  
- **Session restore** via `sessionStorage`  

## Shell

```text
help | sysinfo | ls cd cat write mkdir rm
sudo <cmd> | apx list | apx remove <id> | perms
lsusb | bluetooth scan | network
```

## Packages

```bash
python tools/apx_packager.py --src ./my_app --out ./dist/my.apx \
  --name "My App" --id com.example.app --perms hardware.network.read
```

Samples: `packages/hello-world.apx`, `packages/media-player.apx`

## Documentation

| Doc | Path |
|-----|------|
| Wiki home | [docs/wiki/Home.md](docs/wiki/Home.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Getting started | [docs/wiki/Getting-Started.md](docs/wiki/Getting-Started.md) |

## License

MIT — see [LICENSE](LICENSE).
