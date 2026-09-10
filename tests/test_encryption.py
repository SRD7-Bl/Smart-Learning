from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from Backend.Encryption import EncryptionService


class EncryptionServiceTests(unittest.TestCase):
    def test_migrates_existing_file_key_to_keychain(self) -> None:
        key = Fernet.generate_key()
        with tempfile.TemporaryDirectory() as temp_dir:
            key_path = Path(temp_dir) / ".sl_key"
            key_path.write_bytes(key)

            with (
                patch("Backend.Encryption.keyring.get_password", side_effect=[None, key.decode("ascii")]),
                patch("Backend.Encryption.keyring.set_password") as set_password,
            ):
                service = EncryptionService(key_path)

            set_password.assert_called_once_with(
                "com.smartlearning.app",
                "storage-fernet-key-v1",
                key.decode("ascii"),
            )
            self.assertFalse(key_path.exists())
            self.assertEqual(service.decrypt_to_dict(service.encrypt_dict({"value": 1})), {"value": 1})

    def test_uses_existing_keychain_key(self) -> None:
        key = Fernet.generate_key()
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("Backend.Encryption.keyring.get_password", return_value=key.decode("ascii")),
                patch("Backend.Encryption.keyring.set_password") as set_password,
            ):
                service = EncryptionService(Path(temp_dir) / ".sl_key")

            set_password.assert_not_called()
            self.assertEqual(service.decrypt_to_dict(service.encrypt_dict({"value": 2})), {"value": 2})

    def test_preserves_conflicting_legacy_key(self) -> None:
        keychain_key = Fernet.generate_key()
        legacy_key = Fernet.generate_key()
        with tempfile.TemporaryDirectory() as temp_dir:
            key_path = Path(temp_dir) / ".sl_key"
            key_path.write_bytes(legacy_key)

            with patch(
                "Backend.Encryption.keyring.get_password",
                return_value=keychain_key.decode("ascii"),
            ):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    EncryptionService(key_path)

            self.assertEqual(key_path.read_bytes(), legacy_key)


if __name__ == "__main__":
    unittest.main()
