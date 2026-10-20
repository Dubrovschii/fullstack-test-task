import itertools
import unittest

from src.core.enums import AlertLevel, ScanStatus
from src.services.processing.alert_policy import build_alert
from src.services.processing.scan import scan_file
from tests.legacy import legacy_alert, legacy_scan

MB = 1024 * 1024


class ScanRulesTest(unittest.TestCase):
    def test_clean_file(self):
        verdict = scan_file(original_name="report.docx", size=1024, mime_type="application/msword")
        self.assertEqual(verdict.status, ScanStatus.CLEAN)
        self.assertEqual(verdict.details, "no threats found")
        self.assertFalse(verdict.requires_attention)

    def test_suspicious_extension_is_case_insensitive(self):
        verdict = scan_file(original_name="Setup.EXE", size=10, mime_type="application/octet-stream")
        self.assertEqual(verdict.status, ScanStatus.SUSPICIOUS)
        self.assertEqual(verdict.details, "suspicious extension .exe")
        self.assertTrue(verdict.requires_attention)

    def test_size_threshold_is_strictly_greater_than_10_mb(self):
        self.assertFalse(scan_file(original_name="a.bin", size=10 * MB, mime_type="x/y").requires_attention)
        self.assertTrue(scan_file(original_name="a.bin", size=10 * MB + 1, mime_type="x/y").requires_attention)

    def test_pdf_mime_mismatch(self):
        verdict = scan_file(original_name="a.pdf", size=1, mime_type="text/plain")
        self.assertEqual(verdict.details, "pdf extension does not match mime type")
        for mime in ("application/pdf", "application/octet-stream"):
            self.assertFalse(scan_file(original_name="a.pdf", size=1, mime_type=mime).requires_attention)

    def test_reasons_are_joined_in_the_original_order(self):
        verdict = scan_file(original_name="a.js", size=11 * MB, mime_type="text/javascript")
        self.assertEqual(verdict.details, "suspicious extension .js, file is larger than 10 MB")

    def test_parity_with_original_implementation(self):
        names = ["a.exe", "a.EXE", "a.bat", "a.cmd", "a.sh", "a.js", "a.pdf", "a.PDF", "a.txt", "noext", "a.tar.gz", ".js"]
        sizes = [0, 1, 10 * MB, 10 * MB + 1, 50 * MB]
        mimes = ["application/pdf", "application/octet-stream", "text/plain", "image/png", "application/x-sh"]
        for name, size, mime in itertools.product(names, sizes, mimes):
            with self.subTest(name=name, size=size, mime=mime):
                verdict = scan_file(original_name=name, size=size, mime_type=mime)
                self.assertEqual(
                    (verdict.status.value, verdict.details, verdict.requires_attention),
                    legacy_scan(name, size, mime),
                )


class AlertPolicyTest(unittest.TestCase):
    def test_levels(self):
        failed = build_alert(processing_status="failed", requires_attention=True, scan_details="x")
        self.assertEqual((failed.level, failed.message), (AlertLevel.CRITICAL, "File processing failed"))

        warning = build_alert(processing_status="processed", requires_attention=True, scan_details="why")
        self.assertEqual((warning.level, warning.message), (AlertLevel.WARNING, "File requires attention: why"))

        info = build_alert(processing_status="processed", requires_attention=False, scan_details="no threats found")
        self.assertEqual((info.level, info.message), (AlertLevel.INFO, "File processed successfully"))

    def test_parity_with_original_implementation(self):
        for status, attention, details in itertools.product(
            ["uploaded", "processing", "processed", "failed"], [True, False], [None, "no threats found", "boom"]
        ):
            with self.subTest(status=status, attention=attention, details=details):
                draft = build_alert(processing_status=status, requires_attention=attention, scan_details=details)
                self.assertEqual((draft.level.value, draft.message), legacy_alert(status, attention, details))


if __name__ == "__main__":
    unittest.main()
