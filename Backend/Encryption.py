"""Fernet encryption helpers for Smart Learning local storage."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

import keyring
from cryptography.fernet import Fernet, InvalidToken
from keyring.errors import KeyringError


KEYRING_SERVICE = "com.smartlearning.app"
KEYRING_ACCOUNT = "storage-fernet-key-v1"


class EncryptionService:
    """Encrypt and decrypt JSON-compatible dictionaries with a local Fernet key."""

    def __init__(
        self,
        key_path: Path,
        keyring_service: str = KEYRING_SERVICE,
        keyring_account: str = KEYRING_ACCOUNT,
    ) -> None:
        self.key_path = key_path
        self.keyring_service = keyring_service
        self.keyring_account = keyring_account
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
        keychain_key = self._read_keychain_key()
        if keychain_key is not None:
            self._remove_matching_legacy_key(keychain_key)
            return keychain_key

        legacy_key = self._read_legacy_key()
        key = legacy_key or Fernet.generate_key()
        self._validate_key(key, "legacy key file" if legacy_key else "generated key")
        self._store_keychain_key(key)

        verified_key = self._read_keychain_key()
        if verified_key is None or not secrets.compare_digest(key, verified_key):
            raise ValueError("Encryption key could not be verified after saving it to the system keychain.")

        if legacy_key is not None:
            self._remove_matching_legacy_key(verified_key)

        return verified_key

    def _read_keychain_key(self) -> bytes | None:
        try:
            key_text = keyring.get_password(self.keyring_service, self.keyring_account)
        except KeyringError as error:
            raise ValueError("System keychain could not be accessed.") from error

        if key_text is None:
            return None

        try:
            key = key_text.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("System keychain contains an invalid encryption key.") from error

        self._validate_key(key, "system keychain")
        return key

    def _store_keychain_key(self, key: bytes) -> None:
        try:
            keyring.set_password(
                self.keyring_service,
                self.keyring_account,
                key.decode("ascii"),
            )
        except (KeyringError, UnicodeDecodeError) as error:
            raise ValueError("Encryption key could not be saved to the system keychain.") from error

    def _read_legacy_key(self) -> bytes | None:
        if not self.key_path.exists() or self.key_path.stat().st_size == 0:
            return None

        try:
            key = self.key_path.read_bytes().strip()
        except OSError as error:
            raise ValueError("Legacy encryption key file could not be read.") from error

        self._validate_key(key, "legacy key file")
        return key

    def _remove_matching_legacy_key(self, keychain_key: bytes) -> None:
        if not self.key_path.exists():
            return

        legacy_key = self._read_legacy_key()
        if legacy_key is not None and not secrets.compare_digest(legacy_key, keychain_key):
            raise ValueError(
                "The system keychain key does not match the legacy key file; the legacy file was preserved."
            )

        try:
            self.key_path.unlink()
        except OSError as error:
            raise ValueError("Legacy encryption key file could not be removed after migration.") from error

    def _validate_key(self, key: bytes, source: str) -> None:
        try:
            Fernet(key)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{source.capitalize()} is not a valid Fernet key.") from error
