"""ApexOS Hybrid — HTTP/WebSocket API. UI lives in /static (decoupled DE)."""
import asyncio, secrets, random, json, base64, zipfile, io
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.core.kernel import ApexKernel

ROOT = Path(__file__).resolve().parent.parent.parent
STATIC = ROOT / "static"
APPS_DIR = ROOT / "apps"

app = FastAPI(title="ApexOS Hybrid", version="3.1.0")
kernel = ApexKernel()

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

def discover_apps():
    apps = []
    if APPS_DIR.exists():
        for d in sorted(APPS_DIR.iterdir()):
            if d.is_dir() and (d / "manifest.json").exists():
                try:
                    apps.append(json.loads((d / "manifest.json").read_text(encoding="utf-8")))
                except Exception:
                    pass
    return apps

@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")

@app.get("/api/apps")
async def list_apps():
    return JSONResponse(discover_apps())

@app.get("/api/v1/sys/telemetry")
async def sys_telemetry():
    kernel.sudo.purge_expired()
    return JSONResponse(kernel.telemetry())

@app.post("/api/apx/install")
async def apx_install(file: UploadFile = File(...)):
    try:
        data = await file.read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        manifest = None
        clean = {}
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            base = name.split("/")[-1]
            raw = zf.read(name)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = "[binary]"
            if base == "manifest.json":
                manifest = json.loads(text)
                clean["manifest.json"] = text
            else:
                segs = name.replace("\\", "/").split("/")
                rel = "/".join(segs[1:]) if len(segs) > 1 else segs[0]
                clean[rel] = text
        if not manifest:
            return JSONResponse({"ok": False, "error": "manifest.json not found"}, status_code=400)
        msg = kernel.apx_install_from_json(manifest, clean, grant_perms=False)
        return JSONResponse({"ok": True, "message": msg, "manifest": manifest})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/packages/{app_id}/{file_path:path}")
async def get_package_file(app_id: str, file_path: str):
    path = f"/home/apps/{app_id}/{file_path}"
    content = kernel.vfs.read_file_content(path)
    if content.startswith("cat:"):
        return JSONResponse({"ok": False, "error": "File not found"}, status_code=404)
    media = (
        "text/html" if file_path.endswith(".html") else
        "application/javascript" if file_path.endswith(".js") else
        "application/json" if file_path.endswith(".json") else
        "text/plain"
    )
    from fastapi.responses import Response
    return Response(content=content, media_type=media)

@app.get("/api/permissions")
async def get_perms():
    return JSONResponse(kernel.get_permissions())

@app.post("/api/permissions/grant")
async def grant_perm(body: dict):
    app_id = body.get("app_id", "")
    permission = body.get("permission", "")
    if not app_id or not permission:
        return JSONResponse({"ok": False, "error": "app_id and permission required"}, status_code=400)
    return JSONResponse({"ok": True, "message": kernel.grant_permission(app_id, permission)})

APPS_DIR.mkdir(parents=True, exist_ok=True)
if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
app.mount("/apps", StaticFiles(directory=str(APPS_DIR)), name="apps")

@app.websocket("/ws")
async def handle_ipc(websocket: WebSocket):
    await websocket.accept()
    session_token = ""
    authenticated_user = ""
    try:
        while True:
            packet = await websocket.receive_json()
            token = packet.get("token", "")
            action = packet.get("action")

            if action == "write_file":
                if not token or token != session_token:
                    await websocket.send_json({"output": "Unauthenticated session."})
                    continue
                session = kernel.active_sessions.get(token, {})
                user = session.get("user", "root")
                cwd = session.get("cwd", "/")
                path = kernel.vfs.resolve_path(cwd, packet.get("path", "").strip())
                msg = kernel.vfs.write_file_content(path, packet.get("content", ""), owner=user)
                await websocket.send_json({"output": msg, "user": authenticated_user, "cwd": cwd})
                continue

            if action == "sudo_auth":
                if not token or token != session_token:
                    await websocket.send_json({"output": "Unauthenticated.", "sudo_ok": False})
                    continue
                session = kernel.active_sessions.get(token, {})
                user = session.get("user", "")
                cwd = session.get("cwd", "/")
                if user and kernel.auth.authenticate(user, packet.get("password", "")):
                    elev = kernel.sudo.issue(user=user, target_user="root")
                    await websocket.send_json({
                        "sudo_ok": True, "elev_token": elev["token"], "expires_at": elev["expires_at"],
                        "output": "Elevated to root for 15 minutes.", "user": user, "cwd": cwd,
                    })
                else:
                    await websocket.send_json({"sudo_ok": False, "output": "Sorry, try again.", "user": user, "cwd": cwd})
                continue

            raw = packet.get("raw_input", "").strip()
            parts = raw.split()
            if not parts:
                continue
            cmd, args = parts[0].lower(), parts[1:]

            if cmd == "login":
                if len(args) < 2:
                    await websocket.send_json({"output": "Usage: login [user] [password]"})
                    continue
                if kernel.auth.authenticate(args[0], args[1]):
                    session_token = secrets.token_hex(16)
                    authenticated_user = args[0]
                    kernel.register_session(session_token, args[0])
                    sess = kernel.active_sessions[session_token]
                    await websocket.send_json({
                        "token": session_token, "output": f"Welcome {args[0]}!",
                        "user": args[0], "cwd": sess["cwd"],
                    })
                else:
                    await websocket.send_json({"output": "Access denied: invalid credentials."})
                continue

            if not token or token != session_token:
                await websocket.send_json({"output": "Unauthenticated session."})
                continue

            if cmd == "matrix":
                async def stream_matrix():
                    for _ in range(20):
                        await websocket.send_json({
                            "output": "".join(str(random.randint(0, 1)) for _ in range(56)),
                            "user": authenticated_user,
                            "cwd": kernel.active_sessions.get(token, {}).get("cwd", "/"),
                        })
                        await asyncio.sleep(0.04)
                await kernel.scheduler.spawn("matrix", stream_matrix(), owner=authenticated_user)
                continue

            if cmd == "apx":
                if not args or args[0] == "list":
                    out = kernel.apx_list()
                elif args[0] == "remove" and len(args) > 1:
                    out = kernel.apx_remove(args[1])
                else:
                    out = "Usage: apx list | apx remove <app-id>"
                await websocket.send_json({"output": out, "user": authenticated_user, "cwd": kernel.active_sessions[token]["cwd"]})
                continue

            if cmd in ("perms", "permissions"):
                resp = await kernel.syscall(token, "SYS_PERMS_LIST", args)
                await websocket.send_json({"output": resp.get("output", ""), "user": authenticated_user, "cwd": resp.get("cwd", "/")})
                continue

            if cmd == "help":
                help_text = (
                    "=== ApexOS Hybrid ===\n"
                    "  login whoami pwd date sysinfo help clear\n"
                    "  ls cd cat write touch mkdir rm echo ps kill matrix\n"
                    "  sudo <cmd> | apx list | apx remove <id> | perms\n"
                    "  lsusb | bluetooth scan | network"
                )
                await websocket.send_json({"output": help_text, "user": authenticated_user, "cwd": kernel.active_sessions[token]["cwd"]})
                continue

            syscall_map = {
                "sysinfo": "SYS_INFO", "ps": "SYS_PROCESS_LIST", "kill": "SYS_PROCESS_KILL",
                "ls": "SYS_FS_LIST", "cd": "SYS_FS_CHANGEDIR", "cat": "SYS_FS_READ",
                "write": "SYS_FS_WRITE", "touch": "SYS_FS_TOUCH", "mkdir": "SYS_FS_MKDIR",
                "rm": "SYS_FS_RM", "whoami": "SYS_WHOAMI", "pwd": "SYS_PWD",
                "echo": "SYS_ECHO", "date": "SYS_DATE",
            }
            if cmd in syscall_map:
                resp = await kernel.syscall(token, syscall_map[cmd], args)
                await websocket.send_json({"output": resp.get("output", ""), "user": authenticated_user, "cwd": resp.get("cwd", "/")})
            else:
                await websocket.send_json({
                    "output": f"Shell: {cmd}: command not found. Type 'help'.",
                    "user": authenticated_user, "cwd": kernel.active_sessions[token]["cwd"],
                })
    except WebSocketDisconnect:
        kernel.close_session(session_token)
