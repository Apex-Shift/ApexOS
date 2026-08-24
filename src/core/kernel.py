import time
import json
from datetime import datetime
from typing import Dict, Any
from src.core.scheduler import AsyncScheduler
from src.filesystem.vfs import VirtualFileSystem
from src.auth.rbac import SecuritySubsystem
from src.core.sudo_manager import SudoManager

class ApexKernel:
    def __init__(self):
        self.version = "ApexOS Hybrid Edition v3.0.0"
        self.boot_time = time.time()
        self.scheduler = AsyncScheduler()
        self.vfs = VirtualFileSystem()
        self.auth = SecuritySubsystem()
        self.sudo = SudoManager()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def register_session(self, token: str, username: str) -> None:
        home = f"/home/{username}" if username != "root" else "/root"
        if not self.vfs.directory_exists(home):
            self.vfs.create_directory(home, owner=username)
        self.active_sessions[token] = {
            "user": username,
            "cwd": home if self.vfs.directory_exists(home) else "/",
            "env": {"SHELL": "/bin/sh", "HOME": home, "USER": username, "PATH": "/bin"},
        }

    def close_session(self, token: str) -> None:
        if token in self.active_sessions:
            del self.active_sessions[token]

    def get_permissions(self) -> dict:
        raw = self.vfs.read_file_content("/system/etc/permissions.json")
        try:
            return json.loads(raw) if raw and not raw.startswith("cat:") else {}
        except json.JSONDecodeError:
            return {}

    def set_permissions(self, data: dict) -> None:
        self.vfs.write_file_content("/system/etc/permissions.json", json.dumps(data, indent=2), owner="root")

    def grant_permission(self, app_id: str, permission: str) -> str:
        reg = self.get_permissions()
        reg.setdefault(app_id, {})[permission] = True
        self.set_permissions(reg)
        return f"Granted {permission} to {app_id}"

    def revoke_permission(self, app_id: str, permission: str) -> str:
        reg = self.get_permissions()
        if app_id in reg and permission in reg[app_id]:
            reg[app_id][permission] = False
            self.set_permissions(reg)
            return f"Revoked {permission} from {app_id}"
        return f"Permission {permission} not set for {app_id}"

    def check_permission(self, app_id: str, permission: str) -> bool:
        reg = self.get_permissions()
        return bool(reg.get(app_id, {}).get(permission, False))

    def apx_list(self) -> str:
        apps_path = "/home/apps"
        if not self.vfs.directory_exists(apps_path):
            return "No packages installed."
        content = self.vfs.tree.get(apps_path, {}).get("content", [])
        if not content:
            return "No packages installed."
        lines = ["ID                          VERSION    NAME"]
        lines.append("-" * 50)
        for app_id in sorted(content):
            manifest_path = f"{apps_path}/{app_id}/manifest.json"
            name, version = app_id, "?"
            if self.vfs.exists(manifest_path):
                try:
                    m = json.loads(self.vfs.read_file_content(manifest_path))
                    name = m.get("name", app_id)
                    version = m.get("version", "?")
                except Exception:
                    pass
            lines.append(f"{app_id:<28} {version:<10} {name}")
        return "\n".join(lines)

    def apx_install_from_json(self, manifest: dict, files: dict, grant_perms: bool = False) -> str:
        """Install app from parsed .apx contents (manifest + file map)."""
        app_id = manifest.get("id") or manifest.get("name", "unknown").replace(" ", "_").lower()
        base = f"/home/apps/{app_id}"
        if self.vfs.exists(base):
            self.vfs.remove_tree(base)
        self.vfs.create_directory(base, owner="root")
        # Write manifest
        self.vfs.write_file_content(f"{base}/manifest.json", json.dumps(manifest, indent=2), owner="root")
        # Write other files
        for rel_path, content in files.items():
            if rel_path in ("manifest.json",):
                continue
            full = f"{base}/{rel_path}"
            # ensure parent dirs
            parts = rel_path.split("/")
            if len(parts) > 1:
                acc = base
                for part in parts[:-1]:
                    acc = f"{acc}/{part}"
                    if not self.vfs.directory_exists(acc):
                        self.vfs.create_directory(acc, owner="root")
            self.vfs.write_file_content(full, content, owner="root")
        # Permissions
        perms = manifest.get("permissions", [])
        if grant_perms and perms:
            for p in perms:
                self.grant_permission(app_id, p)
        perm_note = f" Permissions requested: {', '.join(perms)}" if perms else ""
        return f"Installed {app_id} v{manifest.get('version', '?')}.{perm_note}"

    def apx_remove(self, app_id: str) -> str:
        base = f"/home/apps/{app_id}"
        if not self.vfs.exists(base):
            return f"apx: package '{app_id}' not found."
        self.vfs.remove_tree(base)
        reg = self.get_permissions()
        if app_id in reg:
            del reg[app_id]
            self.set_permissions(reg)
        return f"Removed package {app_id}."


    def telemetry(self) -> list:
        import random
        rows = [{
            "pid": 1, "ppid": 0, "name": "system-init", "user": "root",
            "status": "sleeping", "cpu_usage": 0.05,
            "mem_usage": round(12.0 + random.random(), 1),
        }]
        for pid, proc in self.scheduler.table.items():
            rows.append({
                "pid": pid,
                "ppid": 1,
                "name": proc.name,
                "user": getattr(proc, "owner", "root"),
                "status": str(proc.status).lower(),
                "cpu_usage": round(random.uniform(0.1, 3.5), 2),
                "mem_usage": round(random.uniform(8, 48), 1),
            })
        return rows

    async def syscall(self, token: str, identifier: str, params: list) -> Dict[str, Any]:
        if token not in self.active_sessions:
            return {"status": "DENIED", "output": "Authentication error (invalid session).", "cwd": "/"}
        session = self.active_sessions[token]
        user = session["user"]
        cwd = session["cwd"]
        try:
            if identifier == "SYS_PROCESS_LIST":
                return {"status": "SUCCESS", "output": self.scheduler.generate_ps_output(), "cwd": cwd}
            elif identifier == "SYS_PROCESS_KILL":
                if not params:
                    return {"status": "ERROR", "output": "Usage: kill [PID]", "cwd": cwd}
                try:
                    pid = int(params[0])
                except ValueError:
                    return {"status": "ERROR", "output": "Invalid PID.", "cwd": cwd}
                success = await self.scheduler.terminate(pid)
                return {"status": "SUCCESS" if success else "ERROR",
                        "output": f"Process {pid} terminated." if success else f"Unable to kill PID {pid}.", "cwd": cwd}
            elif identifier == "SYS_FS_LIST":
                return {"status": "SUCCESS", "output": self.vfs.list_directory(cwd), "cwd": cwd}
            elif identifier == "SYS_FS_CHANGEDIR":
                target = params[0] if params else session["env"].get("HOME", "/")
                new_path = self.vfs.resolve_path(cwd, target)
                if self.vfs.directory_exists(new_path):
                    session["cwd"] = new_path
                    return {"status": "SUCCESS", "output": "", "cwd": new_path}
                return {"status": "ERROR", "output": f"cd: {target}: No such directory.", "cwd": cwd}
            elif identifier == "SYS_FS_READ":
                if not params:
                    return {"status": "ERROR", "output": "Usage: cat [file]", "cwd": cwd}
                return {"status": "SUCCESS", "output": self.vfs.read_file_content(self.vfs.resolve_path(cwd, params[0])), "cwd": cwd}
            elif identifier == "SYS_FS_WRITE":
                if len(params) < 2:
                    return {"status": "ERROR", "output": "Usage: write [file] [content...]", "cwd": cwd}
                path = self.vfs.resolve_path(cwd, params[0])
                return {"status": "SUCCESS", "output": self.vfs.write_file_content(path, " ".join(params[1:]), owner=user), "cwd": cwd}
            elif identifier == "SYS_FS_TOUCH":
                if not params:
                    return {"status": "ERROR", "output": "Usage: touch [file]", "cwd": cwd}
                return {"status": "SUCCESS", "output": self.vfs.create_file(self.vfs.resolve_path(cwd, params[0]), owner=user), "cwd": cwd}
            elif identifier == "SYS_FS_MKDIR":
                if not params:
                    return {"status": "ERROR", "output": "Usage: mkdir [directory]", "cwd": cwd}
                return {"status": "SUCCESS", "output": self.vfs.create_directory(self.vfs.resolve_path(cwd, params[0]), owner=user), "cwd": cwd}
            elif identifier == "SYS_FS_RM":
                if not params:
                    return {"status": "ERROR", "output": "Usage: rm [file|directory]", "cwd": cwd}
                return {"status": "SUCCESS", "output": self.vfs.remove(self.vfs.resolve_path(cwd, params[0])), "cwd": cwd}
            elif identifier == "SYS_INFO":
                uptime = int(time.time() - self.boot_time)
                h, rem = divmod(uptime, 3600)
                m, s = divmod(rem, 60)
                info = (
                    f"OS          : {self.version}\n"
                    f"Uptime      : {h}h {m}m {s}s\n"
                    f"Filesystem  : Persistent JSON VFS\n"
                    f"Packages    : .apx format + permission gatekeeper\n"
                    f"Hardware    : Web Bluetooth / USB / Network bridge\n"
                    f"Security    : RBAC + app permission registry\n"
                    f"User        : {user}\n"
                    f"Sessions    : {len(self.active_sessions)}"
                )
                return {"status": "SUCCESS", "output": info, "cwd": cwd}
            elif identifier == "SYS_WHOAMI":
                return {"status": "SUCCESS", "output": user, "cwd": cwd}
            elif identifier == "SYS_PWD":
                return {"status": "SUCCESS", "output": cwd, "cwd": cwd}
            elif identifier == "SYS_ECHO":
                return {"status": "SUCCESS", "output": " ".join(params), "cwd": cwd}
            elif identifier == "SYS_DATE":
                return {"status": "SUCCESS", "output": datetime.now().strftime("%a %b %d %Y %H:%M:%S"), "cwd": cwd}
            elif identifier == "SYS_APX_LIST":
                return {"status": "SUCCESS", "output": self.apx_list(), "cwd": cwd}
            elif identifier == "SYS_APX_REMOVE":
                if not params:
                    return {"status": "ERROR", "output": "Usage: apx remove <app-id>", "cwd": cwd}
                return {"status": "SUCCESS", "output": self.apx_remove(params[0]), "cwd": cwd}
            elif identifier == "SYS_PERMS_LIST":
                reg = self.get_permissions()
                if not reg:
                    return {"status": "SUCCESS", "output": "No app permissions granted.", "cwd": cwd}
                lines = []
                for app_id, perms in reg.items():
                    granted = [k for k, v in perms.items() if v]
                    lines.append(f"{app_id}: {', '.join(granted) if granted else '(none)'}")
                return {"status": "SUCCESS", "output": "\n".join(lines), "cwd": cwd}
            return {"status": "UNKNOWN", "output": f"Syscall '{identifier}' not found.", "cwd": cwd}
        except Exception as e:
            return {"status": "CRASH", "output": f"Kernel fatal error: {str(e)}", "cwd": cwd}
