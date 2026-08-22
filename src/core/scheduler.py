import asyncio
import time
from typing import Dict, Any, Optional

class Process:
    def __init__(self, pid: int, name: str, coro, owner: str = "root"):
        self.pid = pid
        self.name = name
        self.coro = coro
        self.status = "READY"
        self.owner = owner
        self.start_time = time.time()
        self.cpu_time = 0.0
        self.task: Optional[asyncio.Task] = None

class AsyncScheduler:
    def __init__(self):
        self.table: Dict[int, Process] = {}
        self.pid_counter = 1

    async def spawn(self, name: str, coro, owner: str = "root") -> int:
        """Register and launch a virtual process in the OS event loop."""
        pid = self.pid_counter
        proc = Process(pid, name, coro, owner)
        self.table[pid] = proc
        self.pid_counter += 1

        proc.status = "RUNNING"
        proc.task = asyncio.create_task(self._wrap_execution(proc))
        return pid

    async def _wrap_execution(self, proc: Process):
        try:
            await proc.coro
            proc.status = "TERMINATED"
        except asyncio.CancelledError:
            proc.status = "KILLED"
        except Exception as e:
            proc.status = f"CRASHED ({type(e).__name__})"
        finally:
            await asyncio.sleep(5)
            if proc.pid in self.table:
                del self.table[proc.pid]

    async def terminate(self, pid: int) -> bool:
        if pid in self.table and self.table[pid].task:
            self.table[pid].task.cancel()
            return True
        return False

    def generate_ps_output(self) -> str:
        if not self.table:
            return "No processes running."

        lines = [f"{'PID':<6} {'PROCESS':<20} {'USER':<10} {'STATUS':<15} {'TIME':<6}"]
        lines.append("-" * 60)
        for pid, p in self.table.items():
            elapsed = int(time.time() - p.start_time)
            lines.append(f"{pid:<6} {p.name:<20} {p.owner:<10} {p.status:<15} {elapsed}s")
        return "\n".join(lines)
