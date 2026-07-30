import json
import smtplib
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import notifiers


UPDATES = [{
    "uid": 123,
    "name": "tester",
    "video": {
        "bvid": "BV1", "title": "new video", "link": "https://example.com/BV1",
        "created": 1700000000, "length": "01:00", "play": 10,
    },
}]


class NotifierTests(unittest.TestCase):
    def settings(self):
        return {
            "up_users": [{"uid": 123, "name": "tester"}],
            "notifications": {
                "email": {"enabled": False},
                "webhook": {
                    "enabled": True, "url": "https://example.com/hook",
                    "headers": {"Authorization": "Bearer test"}, "timeout": 5,
                },
                "gotify": {"enabled": False},
            },
        }

    def test_play_count_uses_readable_chinese_units(self):
        self.assertEqual(notifiers.format_play_count(1_250_000), "125万")
        self.assertEqual(notifiers.format_play_count(890_000), "89万")
        self.assertEqual(notifiers.format_play_count(123), "123")

    @patch("notifiers.urlopen")
    def test_webhook_posts_expected_json_and_headers(self, mocked_urlopen):
        response = MagicMock()
        response.status = 204
        mocked_urlopen.return_value.__enter__.return_value = response

        outcomes = notifiers.send_notifications(
            self.settings(), UPDATES, UPDATES, "2026-07-30T12:00:00+08:00"
        )

        self.assertTrue(outcomes[0]["success"])
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["event"], "bilibili.video.updated")
        self.assertEqual(payload["updates"][0]["bvid"], "BV1")
        self.assertEqual(request.get_header("Authorization"), "Bearer test")

    @patch("notifiers.urlopen")
    def test_webhook_failure_is_reported(self, mocked_urlopen):
        mocked_urlopen.side_effect = OSError("network down")
        outcomes = notifiers.send_notifications(self.settings(), UPDATES, UPDATES, "now")
        self.assertFalse(outcomes[0]["success"])
        self.assertIn("network down", outcomes[0]["error"])

    @patch("notifiers.urlopen")
    def test_post_json_rejects_non_http_scheme_before_opening(self, mocked_urlopen):
        with self.assertRaisesRegex(ValueError, "HTTP"):
            notifiers.post_json("file:///etc/passwd", {"test": True})
        mocked_urlopen.assert_not_called()

    @patch("notifiers.urlopen")
    def test_gotify_uses_token_priority_and_message_endpoint(self, mocked_urlopen):
        response = MagicMock()
        response.status = 200
        mocked_urlopen.return_value.__enter__.return_value = response
        configured = self.settings()
        configured["notifications"]["webhook"]["enabled"] = False
        configured["notifications"]["gotify"] = {
            "enabled": True, "url": "https://gotify.example.com/", "token": "app token",
            "priority": 7, "timeout": 4,
        }

        outcomes = notifiers.send_notifications(configured, UPDATES, UPDATES, "now")

        self.assertTrue(outcomes[0]["success"])
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/message?token=app+token", request.full_url)
        self.assertEqual(json.loads(request.data)["priority"], 7)

    @patch("notifiers.smtplib.SMTP")
    def test_email_smtp_failure_is_reported(self, mocked_smtp):
        mocked_smtp.return_value.__enter__.return_value.login.side_effect = smtplib.SMTPException("denied")
        configured = self.settings()
        configured["notifications"]["webhook"]["enabled"] = False
        configured["notifications"]["email"] = {
            "enabled": True, "smtp_host": "smtp.example.com", "smtp_port": 587,
            "username": "from@example.com", "password": "secret",
            "recipients": ["to@example.com"],
        }
        outcomes = notifiers.send_notifications(configured, UPDATES, UPDATES, "now")
        self.assertFalse(outcomes[0]["success"])


if __name__ == "__main__":
    unittest.main()
