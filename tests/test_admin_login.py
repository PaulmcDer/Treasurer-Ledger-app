import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "Treasurer_App.py"
TAB_LABELS = ["🎫 Entry", "✅ To Do", "💰 50/50", "📖 Ledger", "🔧 Tools", "📥 Download"]


class AdminLoginTest(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
        st.cache_resource.clear()
        self.credentials = patch(
            "google.oauth2.service_account.Credentials.from_service_account_info"
        ).start()
        self.authorize = patch("gspread.authorize").start()
        self.addCleanup(patch.stopall)
        self.addCleanup(st.cache_data.clear)
        self.addCleanup(st.cache_resource.clear)

        self.spreadsheet = self.authorize.return_value.open_by_key.return_value
        self.worksheets = {
            name: MagicMock(name=name)
            for name in ("Treasurer_Ledger", "To_Do", "50-50")
        }
        for worksheet in self.worksheets.values():
            worksheet.get_all_records.return_value = []
        self.spreadsheet.worksheet.side_effect = self.worksheets.__getitem__

        self.app = AppTest.from_file(str(APP_PATH), default_timeout=10)
        self.app.secrets["ADMIN_PIN"] = "123456"
        self.app.secrets["gcp_service_account"] = {"test": "credentials"}

    def assert_locked(self):
        self.assertFalse(self.app.exception, list(self.app.exception))
        self.assertEqual([tab.label for tab in self.app.tabs], [TAB_LABELS[0]])
        self.assertFalse(any(button.label == "Log out" for button in self.app.button))
        self.credentials.assert_not_called()
        self.authorize.assert_not_called()
        for worksheet in self.worksheets.values():
            self.assertEqual(worksheet.mock_calls, [])

    def log_in(self, pin):
        next(field for field in self.app.text_input if field.label == "6-Digit Admin PIN").set_value(pin)
        next(button for button in self.app.button if button.label == "Log in").click()
        self.app.run()

    def test_initially_locked_without_sheets_access(self):
        self.app.run()
        self.assert_locked()

    def test_wrong_pin_stays_locked_without_sheets_access(self):
        self.app.run()
        self.log_in("000000")
        self.assert_locked()

    def test_login_then_logout_removes_access(self):
        self.app.run()
        self.log_in("123456")
        self.assertFalse(self.app.exception, list(self.app.exception))
        self.assertEqual([tab.label for tab in self.app.tabs], TAB_LABELS)
        self.authorize.assert_called()
        self.app.run()
        self.assertFalse(self.app.exception, list(self.app.exception))
        self.assertEqual([tab.label for tab in self.app.tabs], TAB_LABELS)

        self.credentials.reset_mock()
        self.authorize.reset_mock()
        for worksheet in self.worksheets.values():
            worksheet.reset_mock()
        next(button for button in self.app.button if button.label == "Log out").click()
        self.app.run()
        self.assert_locked()
        self.app.run()
        self.assert_locked()


if __name__ == "__main__":
    unittest.main()