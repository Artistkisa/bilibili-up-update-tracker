import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import settings


VALID_YAML = """
up_users:
  - uid: 100
    name: yaml-user
notifications:
  email:
    enabled: true
    username: yaml@example.com
    password: yaml-secret
    recipients: [yaml-to@example.com]
"""


class SettingsTests(unittest.TestCase):
    def write_config(self, directory, content=VALID_YAML):
        path = Path(directory) / "settings.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_precedence_cli_over_environment_over_yaml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory)
            env = {
                "EMAIL_USER": "env@example.com",
                "EMAIL_PASS": "env-secret",
                "EMAIL_TO": "env-to@example.com",
                "UP_USERS_JSON": json.dumps([{"uid": 200, "name": "env-user"}]),
                "NOTIFY_CHANNELS": "email",
            }
            loaded = settings.load_settings([
                "--config", str(path), "--up", "300:cli-user", "--data-file", "cli.json"
            ], env=env)

        self.assertEqual(loaded["up_users"], [{"uid": 300, "name": "cli-user"}])
        self.assertEqual(loaded["notifications"]["email"]["username"], "env@example.com")
        self.assertEqual(loaded["data_file"], (settings.PROJECT_ROOT / "cli.json").resolve())

    def test_notify_cli_enables_only_selected_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, VALID_YAML + """
  webhook:
    enabled: false
    url: https://example.com/hook
""")
            loaded = settings.load_settings(
                ["--config", str(path), "--notify", "webhook"], env={}
            )
        self.assertFalse(loaded["notifications"]["email"]["enabled"])
        self.assertTrue(loaded["notifications"]["webhook"]["enabled"])

    def test_invalid_json_environment_is_rejected(self):
        with self.assertRaisesRegex(settings.ConfigError, "UP_USERS_JSON"):
            settings.load_settings([], env={"UP_USERS_JSON": "not-json"})

    def test_invalid_integer_environment_is_rejected(self):
        with self.assertRaisesRegex(settings.ConfigError, "WEBHOOK_TIMEOUT must be an integer"):
            settings.load_settings([], env={"WEBHOOK_TIMEOUT": "slow"})

    def test_enabled_channel_requires_credentials(self):
        env = {
            "UP_USERS_JSON": '[{"uid":1,"name":"test"}]',
            "NOTIFY_CHANNELS": "gotify",
        }
        with self.assertRaisesRegex(settings.ConfigError, "missing: url, token"):
            settings.load_settings([], env=env)

    def test_non_http_notification_url_is_rejected(self):
        env = {
            "UP_USERS_JSON": '[{"uid":1,"name":"test"}]',
            "NOTIFY_CHANNELS": "webhook",
            "WEBHOOK_URL": "file:///etc/passwd",
        }
        with self.assertRaisesRegex(settings.ConfigError, "absolute http"):
            settings.load_settings([], env=env)

    def test_legacy_config_fallback_warns(self):
        legacy = type("Legacy", (), {
            "UP_LIST": {123: "legacy-user"},
            "DATA_FILE": "legacy.json",
            "EMAIL_CONFIG": {
                "smtp_host": "smtp.example.com", "smtp_port": 587,
                "smtp_user": "legacy@example.com", "smtp_pass": "secret-value",
                "to": ["to@example.com"],
            },
        })
        stderr = StringIO()
        with patch.dict(sys.modules, {"config": legacy}), \
                patch.object(settings, "DEFAULT_CONFIG_FILE", Path("missing-config.yaml")), \
                redirect_stderr(stderr):
            loaded = settings.load_settings([], env={})

        self.assertEqual(loaded["up_users"][0]["name"], "legacy-user")
        self.assertIn("deprecated", stderr.getvalue())

    def test_empty_up_users_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, "notifications: {}\n")
            with self.assertRaisesRegex(settings.ConfigError, "up_users"):
                settings.load_settings(["--config", str(path)], env={})


if __name__ == "__main__":
    unittest.main()
