"""
tests/test_config_persistence.py

Regression Test Suite for Dashboard Configuration Preservation
==============================================================
Validates that AdminDashboard._save_system_settings() preserves existing
configuration keys (such as enable_xfiqa_diagnostics and arbitrary custom/nested
fields) when updating slider parameters, and handles missing or corrupted files safely.

SAFETY GUARANTEES:
- Uses temporary directories exclusively for config.json read/write cycles.
- Production attendance.db, attendance.csv, and threat captures are monitored and NEVER touched.
- GUI toasts and audit logging are mocked to prevent visual or SQLite side effects.
"""

import os
import sys
import json
import hashlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from admin_dashboard import AdminDashboard


def compute_file_sha256(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class TestConfigPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Baseline security monitoring of production files
        cls.db_path = os.path.join(PROJECT_ROOT, "database", "attendance.db")
        cls.csv_path = os.path.join(PROJECT_ROOT, "attendance", "attendance.csv")
        cls.threat_dir = os.path.join(PROJECT_ROOT, "reports", "threat_captures")

        cls.init_db_hash = compute_file_sha256(cls.db_path)
        cls.init_csv_hash = compute_file_sha256(cls.csv_path)
        cls.init_threat_count = len(os.listdir(cls.threat_dir)) if os.path.exists(cls.threat_dir) else 0

    def setUp(self):
        # Create an isolated temporary directory for each test
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = self.temp_dir_obj.name
        self.temp_config_path = os.path.join(self.temp_dir, "config.json")

        # Create a lightweight mock dashboard harness
        self.dashboard = AdminDashboard.__new__(AdminDashboard)
        self.dashboard.base_dir = self.temp_dir
        self.dashboard.colors = {
            "success": "#00D084",
            "danger": "#FF5C5C",
            "buttons": "#2563EB"
        }
        self.dashboard.det_slider = MagicMock()
        self.dashboard.det_slider.get.return_value = 85.0
        self.dashboard.match_slider = MagicMock()
        self.dashboard.match_slider.get.return_value = 88.0

        self.dashboard.show_toast = MagicMock()
        self.dashboard.log_audit_event = MagicMock()

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_01_preserve_enable_xfiqa_false(self):
        """Verify enable_xfiqa_diagnostics: false is preserved during slider update."""
        initial_data = {
            "detection_confidence": 75,
            "match_threshold": 80,
            "enable_xfiqa_diagnostics": False
        }
        with open(self.temp_config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=4)

        self.dashboard.det_slider.get.return_value = 89
        self.dashboard.match_slider.get.return_value = 91

        self.dashboard._save_system_settings()

        self.dashboard.show_toast.assert_called_once_with(
            "Configuration Saved", "AI Vision Engine parameters updated securely.", "#00D084"
        )
        self.dashboard.log_audit_event.assert_called_once()

        with open(self.temp_config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["detection_confidence"], 89)
        self.assertEqual(saved_data["match_threshold"], 91)
        self.assertIn("enable_xfiqa_diagnostics", saved_data)
        self.assertIs(saved_data["enable_xfiqa_diagnostics"], False)

    def test_02_preserve_enable_xfiqa_true(self):
        """Verify enable_xfiqa_diagnostics: true is strictly preserved during slider update."""
        initial_data = {
            "detection_confidence": 75,
            "match_threshold": 80,
            "enable_xfiqa_diagnostics": True
        }
        with open(self.temp_config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=4)

        self.dashboard.det_slider.get.return_value = 82
        self.dashboard.match_slider.get.return_value = 87

        self.dashboard._save_system_settings()

        self.dashboard.show_toast.assert_called_once_with(
            "Configuration Saved", "AI Vision Engine parameters updated securely.", "#00D084"
        )

        with open(self.temp_config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["detection_confidence"], 82)
        self.assertEqual(saved_data["match_threshold"], 87)
        self.assertIn("enable_xfiqa_diagnostics", saved_data)
        self.assertIs(saved_data["enable_xfiqa_diagnostics"], True)

    def test_03_preserve_arbitrary_unrelated_and_nested_keys(self):
        """Verify arbitrary third-party, custom, or nested configuration keys survive."""
        initial_data = {
            "detection_confidence": 70,
            "match_threshold": 75,
            "camera_index": 1,
            "system_profile": "campus_east",
            "thresholds": {"min_eye_ar": 0.28, "max_head_pose_yaw": 15},
            "recipients": ["admin1", "admin2"]
        }
        with open(self.temp_config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=4)

        self.dashboard.det_slider.get.return_value = 92
        self.dashboard.match_slider.get.return_value = 85

        self.dashboard._save_system_settings()

        with open(self.temp_config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["detection_confidence"], 92)
        self.assertEqual(saved_data["match_threshold"], 85)
        self.assertEqual(saved_data["camera_index"], 1)
        self.assertEqual(saved_data["system_profile"], "campus_east")
        self.assertEqual(saved_data["thresholds"], {"min_eye_ar": 0.28, "max_head_pose_yaw": 15})
        self.assertEqual(saved_data["recipients"], ["admin1", "admin2"])

    def test_04_create_valid_file_when_absent(self):
        """Verify that a valid configuration file is created when config.json does not initially exist."""
        self.assertFalse(os.path.exists(self.temp_config_path))

        self.dashboard.det_slider.get.return_value = 84
        self.dashboard.match_slider.get.return_value = 86

        self.dashboard._save_system_settings()

        self.assertTrue(os.path.exists(self.temp_config_path))
        self.dashboard.show_toast.assert_called_once_with(
            "Configuration Saved", "AI Vision Engine parameters updated securely.", "#00D084"
        )

        with open(self.temp_config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data, {
            "detection_confidence": 84,
            "match_threshold": 86
        })

    def test_05_malformed_json_safe_failure_original_bytes_intact(self):
        """Verify that malformed JSON triggers an error toast and does not overwrite original bytes."""
        corrupt_bytes = b"{\n    \"detection_confidence\": 85,\n    SYNTAX_CORRUPT_TRAILING_COMMA,\n"
        with open(self.temp_config_path, "wb") as f:
            f.write(corrupt_bytes)

        self.dashboard._save_system_settings()

        self.dashboard.show_toast.assert_called_once_with(
            "Save Error", "Could not save configuration.", "#FF5C5C"
        )
        self.dashboard.log_audit_event.assert_not_called()

        with open(self.temp_config_path, "rb") as f:
            remaining_bytes = f.read()

        self.assertEqual(remaining_bytes, corrupt_bytes)

    def test_06_non_dictionary_root_safe_failure_no_destructive_overwrite(self):
        """Verify non-dictionary root JSON values (array, string, int) do not overwrite the file."""
        cases = [
            b"[\"item1\", \"item2\", 123]",
            b"\"simple_string_payload\"",
            b"98765"
        ]
        for original_bytes in cases:
            with open(self.temp_config_path, "wb") as f:
                f.write(original_bytes)

            self.dashboard.show_toast.reset_mock()
            self.dashboard.log_audit_event.reset_mock()

            self.dashboard._save_system_settings()

            self.dashboard.show_toast.assert_called_once_with(
                "Save Error", "Could not save configuration.", "#FF5C5C"
            )
            self.dashboard.log_audit_event.assert_not_called()

            with open(self.temp_config_path, "rb") as f:
                remaining_bytes = f.read()

            self.assertEqual(remaining_bytes, original_bytes)

    def test_07_write_failure_does_not_report_success(self):
        """Verify simulated disk write error reports error toast and never reports success."""
        initial_data = {"detection_confidence": 80, "match_threshold": 80}
        with open(self.temp_config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        # Simulate permission/IO error on opening for write
        with patch("builtins.open", side_effect=[
            open(self.temp_config_path, "r", encoding="utf-8"),  # Read succeeds
            IOError("Simulated disk write failure: Access Denied") # Write fails
        ]):
            self.dashboard._save_system_settings()

        self.dashboard.show_toast.assert_called_once_with(
            "Save Error", "Could not save configuration.", "#FF5C5C"
        )
        self.dashboard.log_audit_event.assert_not_called()

    def test_08_slider_values_cast_to_integers(self):
        """Verify float slider outputs (e.g. 85.8) are safely converted to integer percentages."""
        self.dashboard.det_slider.get.return_value = 85.8
        self.dashboard.match_slider.get.return_value = 90.2

        self.dashboard._save_system_settings()

        with open(self.temp_config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["detection_confidence"], 85)
        self.assertEqual(saved_data["match_threshold"], 90)
        self.assertIsInstance(saved_data["detection_confidence"], int)
        self.assertIsInstance(saved_data["match_threshold"], int)

    def test_09_full_dashboard_instance_headless_integration(self):
        """Verify integration with an actual off-screen AdminDashboard instance."""
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            with patch.object(AdminDashboard, "_init_recognition_engine"):
                dashboard = AdminDashboard(root)
                dashboard.base_dir = self.temp_dir

                # Pre-seed config with X-FIQA flag
                seed = {"detection_confidence": 85, "match_threshold": 88, "enable_xfiqa_diagnostics": True}
                with open(self.temp_config_path, "w", encoding="utf-8") as f:
                    json.dump(seed, f, indent=4)

                dashboard.show_system_settings()
                self.assertTrue(hasattr(dashboard, "det_slider"))
                self.assertTrue(hasattr(dashboard, "match_slider"))

                dashboard.det_slider.set(77)
                dashboard.match_slider.set(83)

                with patch.object(dashboard, "show_toast") as mock_toast:
                    with patch.object(dashboard, "log_audit_event") as mock_audit:
                        dashboard._save_system_settings()
                        mock_toast.assert_called_once_with(
                            "Configuration Saved", "AI Vision Engine parameters updated securely.", dashboard.colors["success"]
                        )
                        mock_audit.assert_called_once()

                with open(self.temp_config_path, "r", encoding="utf-8") as f:
                    final_data = json.load(f)

                self.assertEqual(final_data["detection_confidence"], 77)
                self.assertEqual(final_data["match_threshold"], 83)
                self.assertIs(final_data["enable_xfiqa_diagnostics"], True)
        finally:
            root.destroy()

    @classmethod
    def tearDownClass(cls):
        # Verify 100% data integrity of production assets
        post_db_hash = compute_file_sha256(cls.db_path)
        post_csv_hash = compute_file_sha256(cls.csv_path)
        post_threat_count = len(os.listdir(cls.threat_dir)) if os.path.exists(cls.threat_dir) else 0

        assert cls.init_db_hash == post_db_hash, "CRITICAL ERROR: attendance.db was modified during tests!"
        assert cls.init_csv_hash == post_csv_hash, "CRITICAL ERROR: attendance.csv was modified during tests!"
        assert cls.init_threat_count == post_threat_count, "CRITICAL ERROR: threat captures folder was modified!"


if __name__ == "__main__":
    unittest.main()
