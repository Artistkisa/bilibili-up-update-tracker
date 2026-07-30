import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))


class ConfigTests(unittest.TestCase):
    def test_email_config_reads_actions_environment(self):
        env = {
            "EMAIL_SMTP_HOST": "smtp.example.com",
            "EMAIL_SMTP_PORT": "465",
            "EMAIL_USER": "sender@example.com",
            "EMAIL_PASS": "secret",
            "EMAIL_TO": "one@example.com, two@example.com",
        }
        with patch.dict(os.environ, env, clear=False):
            import config
            config = importlib.reload(config)

        self.assertEqual(config.EMAIL_CONFIG["smtp_host"], "smtp.example.com")
        self.assertEqual(config.EMAIL_CONFIG["smtp_port"], 465)
        self.assertEqual(config.EMAIL_CONFIG["smtp_user"], "sender@example.com")
        self.assertEqual(config.EMAIL_CONFIG["smtp_pass"], "secret")
        self.assertEqual(config.EMAIL_CONFIG["to"], ["one@example.com", "two@example.com"])

    def test_default_data_file_is_in_project_data_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            import config
            config = importlib.reload(config)

        expected = SRC_DIR.parent / "data" / "monitor_data.json"
        self.assertEqual(config.DATA_FILE, expected)

    def test_empty_actions_values_use_defaults(self):
        env = {"EMAIL_SMTP_PORT": "", "DATA_FILE": ""}
        with patch.dict(os.environ, env, clear=True):
            import config
            config = importlib.reload(config)

        self.assertEqual(config.EMAIL_CONFIG["smtp_port"], 587)
        self.assertEqual(config.DATA_FILE, SRC_DIR.parent / "data" / "monitor_data.json")


if __name__ == "__main__":
    unittest.main()
