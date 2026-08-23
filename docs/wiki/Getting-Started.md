# Getting Started

## Requirements

- Python **3.10+**
- A modern browser (Chrome or Edge recommended for WebUSB / Web Bluetooth)
- Network access if you use demo media streams or CheerpX-related features

## Install

```bash
git clone https://github.com/YOUR_USERNAME/ApexOS.git
cd ApexOS
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## Run

```bash
python run.py
```

Open **http://127.0.0.1:8000**

You should see:

```text
=========================================================
      APEXOS  —  Hybrid Edition v3.0.0
=========================================================
  → http://127.0.0.1:8000
=========================================================
```

## First login

| Username | Password |
|----------|----------|
| `root`   | `password` |
| `guest`  | `guest`    |

After sign-in, the desktop loads and a Terminal window opens.

## First steps

1. Type `help` in the Terminal  
2. Open **Settings** → Network to see host connectivity  
3. Open **Packages** and install `packages/media-player.apx`  
4. Open **Media** to play audio/video  

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Page loads but login does nothing | Hard refresh (`Ctrl+Shift+R`). Check that WebSocket `/ws` is accepted in server logs. |
| WebUSB / Bluetooth unavailable | Use Chromium-based browser on `localhost` or HTTPS. |
| Port 8000 in use | Change the port in `run.py` / `src/main.py`. |
| Disk errors | Delete `storage/disk.img` and restart to reformat the VFS. |

## Project entry points

| File | Role |
|------|------|
| `run.py` | Recommended launcher |
| `src/main.py` | Alternate entry |
| `src/api/server.py` | HTTP + WebSocket + desktop UI |
| `src/core/kernel.py` | Syscalls, packages, sessions |
