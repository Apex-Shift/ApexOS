# Package System (`.apx`)

ApexOS applications can be distributed as **`.apx`** packages.

## Format

An `.apx` file is a **ZIP** archive:

```text
my-app.apx
├── manifest.json    # required
├── index.html       # optional UI entry
├── index.js         # optional script entry
└── assets/          # optional
```

## Manifest

```json
{
  "name": "Media Player",
  "id": "com.apex.mediaplayer",
  "version": "1.0.0",
  "author": "ApexOS",
  "description": "HTML5 audio and video player",
  "permissions": [
    "hardware.usb.read",
    "filesystem.read"
  ],
  "entry": "index.html",
  "window": {
    "width": 720,
    "height": 480,
    "icon": "🎬"
  }
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique package id (reverse-DNS recommended) |
| `name` | Yes | Display name |
| `version` | Recommended | Semver string |
| `permissions` | No | List of permission keys |
| `entry` | No | Main file (`index.html` / `index.js`) |

## Install flow

1. User selects `.apx` in **Packages**  
2. Server unpacks zip and reads `manifest.json`  
3. Files are written under `/home/apps/<id>/`  
4. Gatekeeper modal lists requested permissions  
5. On **Allow**, grants are stored in `permissions.json`  

## CLI

```text
apx list
apx remove com.apex.mediaplayer
```

## HTTP API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/apx/install` | Multipart upload of `.apx` / `.zip` |
| `GET` | `/api/packages/{id}/{file}` | Serve installed package file |
| `GET` | `/api/permissions` | Permission registry |
| `POST` | `/api/permissions/grant` | Grant one permission |

## Sample packages

| Package | Path |
|---------|------|
| Hello World | `packages/hello-world.apx` |
| Media Player | `packages/media-player.apx` |

## Creating your own package

```bash
mkdir my-tool
# add manifest.json + index.html
cd my-tool
zip -r ../my-tool.apx .
```

Install via the Packages app.
