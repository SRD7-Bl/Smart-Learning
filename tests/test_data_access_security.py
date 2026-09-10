from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from Backend.Data_Access import DataAccessModule


class DataAccessSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.key = Fernet.generate_key().decode("ascii")
        self.keyring_patch = patch("Backend.Encryption.keyring.get_password", return_value=self.key)
        self.keyring_patch.start()

    def tearDown(self) -> None:
        self.keyring_patch.stop()

    def test_existing_credentials_require_current_password_before_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_access = DataAccessModule(storage_dir=Path(temp_dir))
            data_access.update_auth_credentials("old@example.com", "old-password")

            data_access.update_auth_credentials(
                "attacker@example.com",
                "attacker-password",
                current_password="wrong-password",
            )
            auth = data_access._read_user_settings()["auth"]
            self.assertEqual(auth["student_id"], "old@example.com")
            self.assertEqual(auth["password"], "old-password")

            data_access.update_auth_credentials(
                "new@example.com",
                "new-password",
                current_password="old-password",
            )
            auth = data_access._read_user_settings()["auth"]
            self.assertEqual(auth["student_id"], "new@example.com")
            self.assertEqual(auth["password"], "new-password")

    def test_delete_requires_password_and_clears_credentials_and_academic_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_access = DataAccessModule(storage_dir=Path(temp_dir))
            data_access.update_auth_credentials("student@example.com", "current-password")
            data_access.save_academic_info({"courses": [{"name": "Private course"}]})

            data_access.delete_local_data("wrong-password")
            self.assertIn("auth", data_access._read_user_settings())
            self.assertTrue(data_access._read_academic_info()["courses"])

            data_access.delete_local_data("current-password")
            self.assertEqual(
                data_access._read_user_settings(),
                {"auto_login": False, "is_first_use": True},
            )
            self.assertEqual(data_access._read_academic_info(), {})

    def test_password_recovery_reset_clears_data_without_revealing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_access = DataAccessModule(storage_dir=Path(temp_dir))
            data_access.update_auth_credentials("student@example.com", "forgotten-password")
            data_access.save_academic_info({"courses": [{"name": "Private course"}]})

            data_access.reset_local_data()

            self.assertEqual(
                data_access._read_user_settings(),
                {"auto_login": False, "is_first_use": True},
            )
            self.assertEqual(data_access._read_academic_info(), {})


if __name__ == "__main__":
    unittest.main()
