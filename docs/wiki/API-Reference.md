# API Reference

## HTTP

### `GET /`

Returns the desktop HTML application.

### `GET /api/apps`

Lists built-in app manifests from the `apps/` directory.

### `POST /api/apx/install`

Multipart form field `file`: `.apx` or `.zip` package.

**Response**

```json
{
  "ok": true,
  "message": "Installed com.example.app v1.0.0.",
  "manifest": { }
}
```

### `GET /api/packages/{app_id}/{file_path}`

Returns a file from an installed package in the VFS.

### `GET /api/permissions`

Returns the full permission registry JSON.

### `POST /api/permissions/grant`

```json
{
  "app_id": "com.apex.mediaplayer",
  "permission": "hardware.usb.read"
}
```

## WebSocket `/ws`

JSON messages, one command per message.

### Client → server

```json
{
  "token": "<session token or empty before login>",
  "raw_input": "ls"
}
```

Write helper:

```json
{
  "token": "<token>",
  "action": "write_file",
  "path": "/root/notes.txt",
  "content": "hello"
}
```

### Server → client

```json
{
  "token": "…",
  "output": "command result",
  "user": "root",
  "cwd": "/root"
}
```

`token` is present on successful `login`.
