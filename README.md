# ApexOS Hybrid Edition
<img width="1366" height="609" alt="image" src="https://github.com/user-attachments/assets/e91afe37-6a93-4ce4-a7ae-020938327435" />

**A virtual operating system in the browser** — desktop GUI, terminal, packages, and real hardware access via Web APIs.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)

---

## Features

| Area | Capabilities |
|------|----------------|
| **Desktop** | Window manager, taskbar, start menu, icons |
| **Terminal** | Full shell + `apx`, `lsusb`, `bluetooth`, `network` |
| **Files** | Persistent VFS (`storage/disk.img`) |
| **Settings** | Network status, Web Bluetooth, WebUSB, permission registry |
| **Packages** | `.apx` install with Android-style permission gatekeeper |
| **Apps** | Calculator, text editor, browser, system info |
| **Security** | Login (RBAC), per-app permission grants in `/system/etc/permissions.json` |

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/ApexOS.git
cd ApexOS
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8000**

| User | Password |
|------|----------|
| root | password |
| guest | guest |

---

## Hybrid architecture (Web APIs)

ApexOS bridges the virtual desktop to the **host browser**:

- **Network** — `navigator.connection` / `navigator.onLine` (Settings → Network, `network` CLI)
- **Bluetooth** — `navigator.bluetooth` (Settings → Bluetooth, `bluetooth scan`)
- **USB** — `navigator.usb` (Settings → USB, `lsusb`)

Hardware calls are user-gated by the browser. Chrome/Edge on localhost or HTTPS work best.

---

## `.apx` package format

An `.apx` file is a **ZIP** archive:

```text
my-app.apx
├── manifest.json
├── index.js
└── (optional assets)
```

### manifest.json

```json
{
  "name": "Hello World",
  "id": "com.apex.helloworld",
  "version": "1.0.0",
  "author": "ApexOS",
  "permissions": ["hardware.network.read", "hardware.usb.read"],
  "entry": "index.js"
}
```

### Install

1. Open **Packages** on the desktop  
2. Select a `.apx` / `.zip` file  
3. Confirm permissions in the gatekeeper dialog  

CLI:

```text
apx list
apx remove com.apex.helloworld
perms
```

Sample package: `packages/hello-world.apx`

Permissions are stored in the VFS at `/system/etc/permissions.json`.

---

## Shell commands

```text
login / whoami / pwd / date / sysinfo
ls  cd  cat  write  touch  mkdir  rm
echo  ps  kill  matrix  clear
apx list | apx remove <id>
perms
lsusb
bluetooth scan
network
help
```

---

## Project layout

```text
ApexOS/
├── apps/                 # Built-in app manifests
├── packages/             # Sample .apx packages
├── src/
│   ├── api/              # FastAPI + desktop frontend
│   ├── auth/             # Authentication
│   ├── core/             # Kernel, scheduler, apx engine
│   └── filesystem/       # VFS
├── storage/disk.img      # Persistent disk (created at runtime)
├── run.py
├── requirements.txt
└── README.md
```

---

## Roadmap implemented

- [x] Phase 1 — Network / Bluetooth / USB control panels + CLI  
- [x] Phase 2 — `.apx` package format + install API + gatekeeper UI  
- [x] Phase 3 — Permission registry + grant API  
- [x] Phase 4 — `apx`, `lsusb`, `bluetooth scan`, `network` commands  

---

## License

MIT — see [LICENSE](LICENSE).

Web Bluetooth / WebUSB behavior depends on the browser vendor. Use HTTPS or `localhost` for full API access.
