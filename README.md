# ApexOS Hybrid Edition

**A virtual operating system in the browser** — desktop GUI, terminal, packages, hardware Web APIs, **sudo elevation**, and a **Task Manager**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)

---

## Features

| Area | Capabilities |
|------|----------------|
| **Desktop (HexaDE)** | Windows with Haiku-style tabs, yellow focus / red root outline |
| **Terminal** | Shell + `sudo` (masked password, 15 min elevation token) |
| **Task Manager** | Live process table, kill with privilege gates |
| **Files** | Persistent VFS (`storage/disk.img`) |
| **Settings** | Network, Bluetooth, USB, permissions |
| **Packages** | `.apx` install + gatekeeper |
| **Media** | HTML5 audio/video player package |
| **Security** | Login, session tokens, sudo elevation, app permissions |

---

## Quick start

```bash
git clone https://github.com/apex-shift/ApexOS.git
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

## Sudo elevation

```text
guest@apexos:~$ sudo sysinfo
[sudo] password for guest: ********
Elevated to root for 15 minutes.
```

- Terminal title bar turns **red** (HexaDE root mode)
- Token lasts **15 minutes**, then expires automatically
- Task Manager → **Sudo mode** unlocks killing root-owned tasks

---

## Task Manager

Desktop icon **Tasks** — telemetry from `/api/v1/sys/telemetry` (1s refresh).

Guest cannot end root processes without elevation.

---

## Packages (`.apx`)

```bash
python tools/apx_packager.py --src ./my_app --out ./dist/my_app.apx \
  --name "My App" --id com.example.myapp --perms hardware.network.read
```

Sample packages: `packages/hello-world.apx`, `packages/media-player.apx`

---

## Shell commands

```text
login / whoami / pwd / date / sysinfo / help
ls  cd  cat  write  touch  mkdir  rm
echo  ps  kill  matrix  clear
sudo <command>
apx list | apx remove <id>
perms
lsusb | bluetooth scan | network
```

---

## Wiki

Full documentation in English: [`docs/wiki/Home.md`](docs/wiki/Home.md)

---

## License

MIT — see [LICENSE](LICENSE).
