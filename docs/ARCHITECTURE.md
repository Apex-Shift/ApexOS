# ApexOS Architecture

## Layers

1. **Core (Python)** — authentication, VFS, scheduler, sudo tokens, package install, syscalls over WebSocket.  
2. **Host bridge (`apex-host.js`)** — session token, WebSocket reconnect, command/send helpers.  
3. **Desktop Environment (`hexade-de.js` + `hexade.css`)** — Deskbar, windows, icons, context menu, apps.

The core never imports DE code. The DE never implements syscalls; it only talks to `ApexHost` and REST.

## HexaDE

- Top **Deskbar** (not a Windows taskbar)  
- Haiku-style yellow accent; **red** under sudo elevation  
- Calendar popover, optional USB/BT buttons  
- Right-click desktop / icons  

To add another DE later: add `static/de/<name>/` and switch the scripts loaded by `index.html`.

## Security model

- Login issues a session token  
- `sudo` issues an ephemeral elevation token (default 15 minutes)  
- `.apx` permissions stored in VFS `/system/etc/permissions.json`  
- Browser hardware APIs still require user gestures and browser prompts  

## WebSocket protocol

Client → server:

```json
{ "token": "<session>", "raw_input": "ls" }
{ "token": "<session>", "action": "sudo_auth", "password": "..." }
{ "token": "<session>", "action": "write_file", "path": "/tmp/a", "content": "hi" }
```

Server → client: `{ "output", "user", "cwd", "token?", "sudo_ok?", "elev_token?" }`.
