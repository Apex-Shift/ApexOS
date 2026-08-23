# Security Model

## Authentication

- Credentials checked in `SecuritySubsystem` (`src/auth/rbac.py`)  
- Passwords stored as **SHA-256** hashes (demo-grade, not production identity)  
- Successful login issues a random **session token**  

## Sessions

- Token maps to `{ user, cwd, env }` in the kernel  
- WebSocket messages must include a valid token for privileged actions  
- Disconnect closes the session  

## App permissions

Installed packages declare permissions in `manifest.json`. Examples:

| Permission | Intended meaning |
|------------|------------------|
| `hardware.usb.read` | May use WebUSB |
| `hardware.bluetooth.scan` | May scan BLE |
| `hardware.network.read` | May read network status |
| `filesystem.read` | May read VFS paths |

Grants are stored in:

```text
/system/etc/permissions.json
```

The Packages **gatekeeper** asks the user before granting.

## Threat model (honest)

ApexOS is an **educational / demo** OS:

- UI and server are same-origin; this is not a multi-tenant hardened host  
- VFS isolation is logical, not a kernel sandbox  
- Do not expose a public deployment without additional hardening  

## Headers

The server sets COOP / COEP-related headers to support advanced browser features where possible. Prefer `localhost` for development.
