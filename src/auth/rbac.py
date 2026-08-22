import hashlib
from typing import Dict

class SecuritySubsystem:
    def __init__(self):
        # Base d'utilisateurs interne simulée (Mots de passe hachés en SHA-256)
        # root:password / guest:guest
        self.shadow_file: Dict[str, str] = {
            "root": hashlib.sha256("password".encode()).hexdigest(),
            "guest": hashlib.sha256("guest".encode()).hexdigest()
        }

    def authenticate(self, username: str, password_raw: str) -> bool:
        """Vérifie les informations d'identification via cryptographie SHA-256."""
        if username not in self.shadow_file:
            return False
        hashed = hashlib.sha256(password_raw.encode()).hexdigest()
        return self.shadow_file[username] == hashed
