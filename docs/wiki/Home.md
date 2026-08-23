# ApexOS Wiki

**ApexOS Hybrid Edition** is a virtual operating system that runs in the browser. It provides a desktop environment, terminal, virtual filesystem, package system (`.apx`), and bridges to real device capabilities through Web APIs.

| | |
|---|---|
| **Edition** | Hybrid v3.0.0 |
| **Stack** | Python · FastAPI · WebSocket · Vanilla JS |
| **License** | MIT |

## Wiki pages

| Page | Description |
|------|-------------|
| [Getting Started](Getting-Started) | Install, run, first login |
| [Architecture](Architecture) | Kernel, VFS, sessions, frontend |
| [Desktop Environment](Desktop-Environment) | Windows, taskbar, built-in apps |
| [Terminal & Shell](Terminal-and-Shell) | Commands reference |
| [Virtual Filesystem](Virtual-Filesystem) | Disk layout and persistence |
| [Package System](Package-System) | `.apx` format, install, permissions |
| [Hardware Bridge](Hardware-Bridge) | Network, Bluetooth, USB |
| [Security Model](Security-Model) | Auth, sessions, app permissions |
| [API Reference](API-Reference) | HTTP and WebSocket protocols |
| [Contributing](Contributing) | How to extend ApexOS |

## Quick links

- Repository README: see project root `README.md`
- Sample packages: `packages/hello-world.apx`, `packages/media-player.apx`
- Default login: `root` / `password`
