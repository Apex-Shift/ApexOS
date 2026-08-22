import json
import os
from typing import Dict, Any, List

class VirtualFileSystem:
    def __init__(self, storage_path: str = "storage/disk.img"):
        self.storage_path = storage_path
        self.tree: Dict[str, Any] = {}
        self._initialize_storage_layer()

    def _initialize_storage_layer(self):
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "files" in data:
                    self.tree = data["files"]
                else:
                    self.tree = data
                return
            except (json.JSONDecodeError, IOError):
                pass
        self._format_raw_disk()

    def _format_raw_disk(self):
        self.tree = {
            "/": {
                "type": "dir",
                "content": ["bin", "home", "root", "readme.txt"],
                "owner": "root"
            },
            "/readme.txt": {
                "type": "file",
                "content": "Welcome to ApexOS!\nA virtual operating system streamed in your browser.",
                "owner": "root"
            },
            "/bin": {
                "type": "dir",
                "content": ["matrix", "sysinfo", "ps"],
                "owner": "root"
            },
            "/home": {
                "type": "dir",
                "content": [],
                "owner": "root"
            },
            "/root": {
                "type": "dir",
                "content": [".bashrc"],
                "owner": "root"
            },
            "/root/.bashrc": {
                "type": "file",
                "content": "alias ll='ls -la'\nexport PATH=/bin",
                "owner": "root"
            }
        }
        self._commit()

    def _commit(self):
        data = {
            "metadata": {
                "label": "APEXOS_DISK",
                "block_size": 512,
                "total_blocks": 2048,
                "used_blocks": len(self.tree)
            },
            "files": self.tree
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def resolve_path(self, cwd: str, target: str) -> str:
        if not target or target == ".":
            return cwd
        if target.startswith("/"):
            computed = target
        else:
            computed = (cwd.rstrip("/") + "/" + target) if cwd != "/" else ("/" + target)

        parts = computed.split("/")
        resolved: List[str] = []
        for p in parts:
            if p == "" or p == ".":
                continue
            if p == "..":
                if resolved:
                    resolved.pop()
            else:
                resolved.append(p)
        return "/" + "/".join(resolved) if resolved else "/"

    def exists(self, path: str) -> bool:
        return path in self.tree

    def directory_exists(self, path: str) -> bool:
        node = self.tree.get(path)
        return bool(node and node.get("type") == "dir")

    def is_file(self, path: str) -> bool:
        node = self.tree.get(path)
        return bool(node and node.get("type") == "file")

    def list_directory(self, path: str) -> str:
        node = self.tree.get(path)
        if not node or node.get("type") != "dir":
            return f"ls: cannot access '{path}': Not a directory."

        content = node.get("content", [])
        if not content:
            return "(empty directory)"

        items = []
        for item in sorted(content):
            item_path = f"{path.rstrip('/')}/{item}" if path != "/" else f"/{item}"
            if self.directory_exists(item_path):
                items.append(f"[{item}/]")
            else:
                items.append(item)
        return "  ".join(items)

    def read_file_content(self, path: str) -> str:
        node = self.tree.get(path)
        if node and node.get("type") == "file":
            return node.get("content", "")
        return f"cat: {path}: No such file or directory."

    def write_file_content(self, path: str, content: str, owner: str = "root") -> str:
        parts = path.rstrip("/").split("/")
        filename = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        if parent_path == "//":
            parent_path = "/"

        if not self.directory_exists(parent_path):
            return f"Error: parent directory '{parent_path}' does not exist."

        parent = self.tree[parent_path]
        if filename not in parent.get("content", []):
            parent.setdefault("content", []).append(filename)

        self.tree[path] = {
            "type": "file",
            "content": content,
            "owner": owner
        }
        self._commit()
        return f"Wrote to {path}."

    def create_file(self, path: str, owner: str = "root") -> str:
        if self.exists(path):
            return f"touch: {path}: File already exists."
        return self.write_file_content(path, "", owner)

    def create_directory(self, path: str, owner: str = "root") -> str:
        if self.exists(path):
            return f"mkdir: {path}: File or directory already exists."

        parts = path.rstrip("/").split("/")
        dirname = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        if parent_path == "//":
            parent_path = "/"

        if not self.directory_exists(parent_path):
            return f"mkdir: {parent_path}: Parent directory not found."

        self.tree[parent_path].setdefault("content", []).append(dirname)
        self.tree[path] = {
            "type": "dir",
            "content": [],
            "owner": owner
        }
        self._commit()
        return f"Directory {path} created."

    def remove(self, path: str) -> str:
        if path == "/":
            return "rm: cannot remove root directory."

        if not self.exists(path):
            return f"rm: {path}: No such file or directory."

        node = self.tree[path]
        if node.get("type") == "dir" and node.get("content"):
            return f"rm: {path}: Directory not empty."

        parts = path.rstrip("/").split("/")
        name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        if parent_path == "//":
            parent_path = "/"

        if parent_path in self.tree and name in self.tree[parent_path].get("content", []):
            self.tree[parent_path]["content"].remove(name)

        del self.tree[path]
        self._commit()
        return f"{path} removed."
