import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import monitor


class MonitorStateTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "lastCheck": None,
            "upData": {"123": {"lastBvid": "BV-old", "lastTitle": "old", "upName": "tester"}},
            "updateCount": 2,
        }
        self.updates = [{
            "uid": 123, "name": "tester", "success": True,
            "video": {"bvid": "BV-new", "title": "new"},
        }]

    def test_failed_notification_does_not_commit_update(self):
        committed = monitor.commit_updates_after_notification(self.data, self.updates, False)
        self.assertFalse(committed)
        self.assertEqual(self.data["upData"]["123"]["lastBvid"], "BV-old")

    def test_all_notifications_success_commits_update(self):
        committed = monitor.commit_updates_after_notification(self.data, self.updates, True)
        self.assertTrue(committed)
        self.assertEqual(self.data["upData"]["123"]["lastBvid"], "BV-new")
        self.assertEqual(self.data["updateCount"], 3)

    def test_save_data_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "monitor.json"
            self.assertTrue(monitor.save_data(self.data, target))
            self.assertTrue(target.exists())
            self.assertFalse(target.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
