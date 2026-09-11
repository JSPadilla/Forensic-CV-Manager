from __future__ import annotations

import unittest
from unittest.mock import patch

import app_config
from update_checker import check_github_release


class UpdateCheckerTests(unittest.TestCase):
    def test_repository_is_configured(self):
        self.assertEqual(app_config.GITHUB_REPOSITORY, "JSPadilla/Forensic-CV-Manager")

    @patch("update_checker._request_json")
    def test_newer_release_is_detected(self, request_json):
        request_json.return_value = {
            "tag_name": "v2.6.0",
            "html_url": "https://github.com/JSPadilla/Forensic-CV-Manager/releases/tag/v2.6.0",
        }
        result = check_github_release("JSPadilla/Forensic-CV-Manager", "2.5.0")
        self.assertTrue(result.update_available)
        self.assertEqual(result.latest_version, "v2.6.0")

    @patch("update_checker._request_json")
    def test_older_release_does_not_trigger_update(self, request_json):
        request_json.return_value = {
            "tag_name": "v2.4.0",
            "html_url": "https://github.com/JSPadilla/Forensic-CV-Manager/releases/tag/v2.4.0",
        }
        result = check_github_release("JSPadilla/Forensic-CV-Manager", "2.5.0")
        self.assertFalse(result.update_available)
        self.assertEqual(result.latest_version, "v2.4.0")


if __name__ == "__main__":
    unittest.main()
