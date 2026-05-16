"""Fernet encryption helpers for Smart Learning local storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    """Encrypt and decrypt JSON-compatible dictionaries with a local Fernet key."""

    def __init__(self, key_path: Path) -> None:
        self.key_path = key_path
        self.fernet = Fernet(self._load_or_create_key())

    def encrypt_dict(self, data: dict[str, Any]) -> str:
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return self.fernet.encrypt(payload).decode("utf-8")

    def decrypt_to_dict(self, token: str) -> dict[str, Any]:
        try:
            payload = self.fernet.decrypt(token.encode("utf-8"))
            data = json.loads(payload.decode("utf-8"))
        except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Encrypted local data could not be decrypted.") from error

        if not isinstance(data, dict):
            raise ValueError("Encrypted local data must contain a JSON object.")

        return data

    def _load_or_create_key(self) -> bytes:
        if self.key_path.exists() and self.key_path.stat().st_size > 0:
            return self.key_path.read_bytes().strip()

        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        return key
