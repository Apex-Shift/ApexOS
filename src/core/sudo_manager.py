"""Ephemeral privilege-elevation tokens for ApexOS."""
from __future__ import annotations
import secrets
import time
from typing import Dict, List, Optional

DEFAULT_TTL = 15 * 60
DEFAULT_SCOPE = ["vfs.system.write", "process.kill", "hardware.usb.admin"]

class SudoManager:
    def __init__(self):
        self._tokens: Dict[str, dict] = {}

    def issue(self, user: str, target_user: str = "root", ttl: int = DEFAULT_TTL,
              scope: Optional[List[str]] = None, target_pid: int = 0) -> dict:
        token = "apex_elev_" + secrets.token_hex(8)
        entry = {
            "target_pid": target_pid,
            "user": target_user,
            "elevated_from": user,
            "token": token,
            "expires_at": int(time.time()) + ttl,
            "scope": scope or list(DEFAULT_SCOPE),
        }
        self._tokens[token] = entry
        return entry

    def validate(self, token: str, required_scope: Optional[str] = None) -> Optional[dict]:
        entry = self._tokens.get(token)
        if not entry:
            return None
        if entry["expires_at"] < time.time():
            del self._tokens[token]
            return None
        if required_scope and required_scope not in entry.get("scope", []):
            return None
        return entry

    def revoke(self, token: str) -> bool:
        return self._tokens.pop(token, None) is not None

    def purge_expired(self) -> None:
        now = time.time()
        for k in [k for k, v in self._tokens.items() if v["expires_at"] < now]:
            del self._tokens[k]
