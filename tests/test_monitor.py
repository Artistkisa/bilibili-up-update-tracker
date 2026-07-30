import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import monitor


class UpdateStateTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "lastCheck": None,
            "upData": {
                "123": {
                    "lastBvid": "BV-old",
                    "lastTitle": "old title",
                    "upName": "tester",
                }
            },
            "updateCount": 2,
        }
        self.updates = [{
            "uid": 123,
            "name": "tester",
            "success": True,
            "video": {"bvid": "BV-new", "title": "new title"},
        }]

    def test_failed_notification_does_not_commit_update(self):
        committed = monitor.commit_updates_after_notification(
            self.data, self.updates, notification_sent=False
        )

        self.assertFalse(committed)
        self.assertEqual(self.data["upData"]["123"]["lastBvid"], "BV-old")
        self.assertEqual(self.data["updateCount"], 2)

    def test_successful_notification_commits_update(self):
        committed = monitor.commit_updates_after_notification(
            self.data, self.updates, notification_sent=True
        )

        self.assertTrue(committed)
        self.assertEqual(self.data["upData"]["123"]["lastBvid"], "BV-new")
        self.assertEqual(self.data["upData"]["123"]["lastTitle"], "new title")
        self.assertEqual(self.data["updateCount"], 3)

    def test_commit_creates_missing_up_state_defensively(self):
        self.data["upData"].clear()

        committed = monitor.commit_updates_after_notification(
            self.data, self.updates, notification_sent=True
        )

        self.assertTrue(committed)
        self.assertEqual(self.data["upData"]["123"]["lastBvid"], "BV-new")


class SaveDataTests(unittest.TestCase):
    def test_save_data_replaces_target_without_leaving_temp_file(self):
        original_data_file = monitor.DATA_FILE
        try:
            with tempfile.TemporaryDirectory() as directory:
                data_file = Path(directory) / "monitor_data.json"
                monitor.DATA_FILE = data_file

                saved = monitor.save_data({"upData": {}, "updateCount": 0})

                self.assertTrue(saved)
                self.assertTrue(data_file.exists())
                self.assertFalse(data_file.with_suffix(".json.tmp").exists())
        finally:
            monitor.DATA_FILE = original_data_file


if __name__ == "__main__":
    unittest.main()
