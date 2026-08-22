import time
from datetime import datetime
from typing import Dict, Any
from src.core.scheduler import AsyncScheduler
from src.filesystem.vfs import VirtualFileSystem
from src.auth.rbac import SecuritySubsystem

class ApexKernel:
    def __init__(self):
        self.version = "ApexOS Core v2.2.0 (Desktop Edition)"
        self.boot_time = time.time()
        self.scheduler = AsyncScheduler()
        self.vfs = VirtualFileSystem()
        self.auth = SecuritySubsystem()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def register_session(self, token: str, username: str) -> None:
        home = f"/home/{username}" if username != "root" else "/root"
        if not self.vfs.directory_exists(home):
            self.vfs.create_directory(home, owner=username)
        self.active_sessions[token] = {
            "user": username,
            "cwd": home if self.vfs.directory_exists(home) else "/",
            "env": {
                "SHELL": "/bin/sh",
                "HOME": home,
                "USER": username,
                "PATH": "/bin"
            }
        }

    def close_session(self, token: str) -> None:
        if token in self.active_sessions:
            del self.active_sessions[token]

    async def syscall(self, token: str, identifier: str, params: list) -> Dict[str, Any]:
        """Unified system call interface for ApexOS."""
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
                return {
                    "status": "SUCCESS" if success else "ERROR",
                    "output": f"Process {pid} terminated." if success else f"Unable to kill PID {pid}.",
                    "cwd": cwd
                }

            elif identifier == "SYS_FS_LIST":
                output = self.vfs.list_directory(cwd)
                return {"status": "SUCCESS", "output": output, "cwd": cwd}

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
                file_path = self.vfs.resolve_path(cwd, params[0])
                content = self.vfs.read_file_content(file_path)
                return {"status": "SUCCESS", "output": content, "cwd": cwd}

            elif identifier == "SYS_FS_WRITE":
                if len(params) < 2:
                    return {"status": "ERROR", "output": "Usage: write [file] [content...]", "cwd": cwd}
                filename = params[0]
                content = " ".join(params[1:])
                file_path = self.vfs.resolve_path(cwd, filename)
                msg = self.vfs.write_file_content(file_path, content, owner=user)
                return {"status": "SUCCESS", "output": msg, "cwd": cwd}

            elif identifier == "SYS_FS_TOUCH":
                if not params:
                    return {"status": "ERROR", "output": "Usage: touch [file]", "cwd": cwd}
                file_path = self.vfs.resolve_path(cwd, params[0])
                msg = self.vfs.create_file(file_path, owner=user)
                return {"status": "SUCCESS", "output": msg, "cwd": cwd}

            elif identifier == "SYS_FS_MKDIR":
                if not params:
                    return {"status": "ERROR", "output": "Usage: mkdir [directory]", "cwd": cwd}
                dir_path = self.vfs.resolve_path(cwd, params[0])
                msg = self.vfs.create_directory(dir_path, owner=user)
                return {"status": "SUCCESS", "output": msg, "cwd": cwd}

            elif identifier == "SYS_FS_RM":
                if not params:
                    return {"status": "ERROR", "output": "Usage: rm [file|directory]", "cwd": cwd}
                target_path = self.vfs.resolve_path(cwd, params[0])
                msg = self.vfs.remove(target_path)
                return {"status": "SUCCESS", "output": msg, "cwd": cwd}

            elif identifier == "SYS_INFO":
                uptime = int(time.time() - self.boot_time)
                hours, rem = divmod(uptime, 3600)
                mins, secs = divmod(rem, 60)
                info_str = (
                    f"OS          : {self.version}\n"
                    f"Uptime      : {hours}h {mins}m {secs}s\n"
                    f"Filesystem  : Persistent JSON Block Layer\n"
                    f"Security    : RBAC Active\n"
                    f"User        : {user}\n"
                    f"Sessions    : {len(self.active_sessions)}"
                )
                return {"status": "SUCCESS", "output": info_str, "cwd": cwd}

            elif identifier == "SYS_WHOAMI":
                return {"status": "SUCCESS", "output": user, "cwd": cwd}

            elif identifier == "SYS_PWD":
                return {"status": "SUCCESS", "output": cwd, "cwd": cwd}

            elif identifier == "SYS_ECHO":
                return {"status": "SUCCESS", "output": " ".join(params), "cwd": cwd}

            elif identifier == "SYS_DATE":
                return {"status": "SUCCESS", "output": datetime.now().strftime("%a %b %d %Y %H:%M:%S"), "cwd": cwd}

            return {"status": "UNKNOWN", "output": f"Syscall '{identifier}' not found.", "cwd": cwd}

        except Exception as e:
            return {"status": "CRASH", "output": f"Kernel fatal error: {str(e)}", "cwd": cwd}
