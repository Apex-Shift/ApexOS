# Architecture

ApexOS is a **hybrid** system: the OS simulation runs on a Python server, while the desktop UI and hardware access run in the browser.

```text
┌─────────────────────────────────────────────────────────┐
│  Browser                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Desktop UI   │  │ Web APIs     │  │ .apx app HTML  │ │
│  │ (windows,    │  │ Network      │  │ (sandboxed     │ │
│  │  terminal)   │  │ Bluetooth    │  │  iframe)       │ │
│  │              │  │ USB          │  │                │ │
│  └──────┬───────┘  └──────────────┘  └────────────────┘ │
│         │ WebSocket + HTTP                               │
└─────────┼───────────────────────────────────────────────┘
          ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI server                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │ Kernel     │  │ VFS        │  │ Auth / sessions    │ │
│  │ syscalls   │  │ disk.img   │  │ RBAC               │ │
│  │ apx engine │  │            │  │ permissions.json   │ │
│  └────────────┘  └────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Components

### Kernel (`src/core/kernel.py`)

- Session registry (token → user, cwd, env)
- Syscall dispatcher (`SYS_FS_*`, `SYS_INFO`, …)
- Package install/remove (`apx_*`)
- Permission registry helpers

### Scheduler (`src/core/scheduler.py`)

Lightweight async process table for background tasks (e.g. `matrix`).

### Virtual filesystem (`src/filesystem/vfs.py`)

JSON-backed tree persisted to `storage/disk.img`.

### Auth (`src/auth/rbac.py`)

SHA-256 password verification for built-in accounts.

### API / UI (`src/api/server.py`)

- Serves the single-page desktop
- WebSocket command channel
- REST helpers for packages and permissions

## Design principles

1. **Server owns truth** — filesystem and auth live in Python  
2. **Browser owns interaction** — windows, Web APIs, media  
3. **Explicit permissions** — apps declare needs in `manifest.json`  
4. **Simple packaging** — `.apx` is a zip + manifest  

## Data flow (shell command)

```text
User types "ls"
  → Terminal JS sends WebSocket { token, raw_input: "ls" }
  → Server maps "ls" → SYS_FS_LIST
  → Kernel reads VFS at session cwd
  → Response { output, user, cwd }
  → Terminal appends output
```
