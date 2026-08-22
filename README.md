# ApexOS

**A virtual operating system streamed entirely in your browser.**

ApexOS simulates a kernel, persistent filesystem, process scheduler, and a full desktop GUI — all built with Python, FastAPI, WebSocket, and vanilla HTML/JS.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)

---

## Features

| Component | Description |
|-----------|-------------|
| **Desktop GUI** | Window manager, taskbar, start menu, desktop icons |
| **Terminal** | Full shell with command history |
| **File Explorer** | Browse, create, delete files & folders |
| **Text Editor** | Open / edit / save files |
| **Calculator** | Classic calculator app |
| **Web Browser** | Browse the internet inside ApexOS |
| **Kernel** | Async syscalls, sessions, RBAC auth |
| **VFS** | Persistent virtual filesystem (`storage/disk.img`) |
| **Scheduler** | Virtual process spawn / kill / ps |
| **Addon system** | Drop apps into the `apps/` folder |

---

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/ApexOS.git
cd ApexOS

# Install
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
python run.py
```

Open **http://127.0.0.1:8000**

### Default credentials

| User  | Password |
|-------|----------|
| root  | password |
| guest | guest    |

---

## Shell Commands

```
login [user] [pass]     Authenticate
whoami / pwd / date     Session info
sysinfo                 System information
ls / cd / cat           Navigate & read
write / touch / mkdir   Create & write
rm                      Delete
echo / ps / kill        Utilities
matrix                  Fun daemon
clear                   Clear terminal
help                    List commands
```

---

## Project Structure

```
ApexOS/
├── apps/                  # Addon applications
│   ├── calculator/
│   ├── text_editor/
│   └── sysinfo/
├── src/
│   ├── api/               # FastAPI server + desktop frontend
│   ├── auth/              # Authentication (RBAC)
│   ├── core/              # Kernel + process scheduler
│   └── filesystem/        # Virtual filesystem (VFS)
├── storage/
│   └── disk.img           # Persistent disk image (JSON)
├── config/                # Config stubs
├── tests/                 # Tests (stubs)
├── run.py                 # Easy launcher
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Adding Apps (Addons)

Apps live in the `apps/` directory. Each app is a folder with a `manifest.json`:

```
apps/
└── my_app/
    ├── manifest.json
    └── app.js
```

**manifest.json example:**

```json
{
  "id": "my_app",
  "name": "My App",
  "icon": "🚀",
  "version": "1.0.0",
  "window": { "width": 500, "height": 400 },
  "desktop": true,
  "entry": "app.js"
}
```

The server exposes discovered apps at `GET /api/apps` and serves static files under `/apps/`.

Built-in apps (Terminal, Files, Browser, Calculator, Editor, System) are currently embedded in the desktop for stability. The addon pipeline is ready for extension.

---

## Architecture

```
Browser (Desktop GUI)
    │  WebSocket
    ▼
FastAPI Server  ──►  ApexKernel
                        ├── Auth (RBAC)
                        ├── Scheduler (async processes)
                        └── VFS (persistent JSON disk)
```

- **Frontend**: Pure HTML/CSS/JS window manager
- **Transport**: WebSocket JSON messages (syscalls + file writes)
- **Backend**: Python asyncio kernel with session tokens

---

## Tech Stack

- **Python 3.10+**
- **FastAPI** + **Uvicorn**
- **WebSockets**
- Vanilla JS (no framework)

---

## License

MIT — see [LICENSE](LICENSE).

---

Built with ❤️ in Python.
