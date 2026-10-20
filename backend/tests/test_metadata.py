import random
import tempfile
import unittest
from pathlib import Path

from src.services.processing.metadata import count_pdf_pages, count_text, extract_metadata
from tests.legacy import legacy_pdf_pages, legacy_text_counts

# Characters that matter: every str.splitlines() boundary, CR/CRLF (translated on read),
# multi-byte letters (may be split between chunks) and plain text.
_ALPHABET = ["a", "b", " ", "я", "€", "😀", "\n", "\r", "\r\n", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " "]


class TextCountTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = Path(self._dir.name) / "sample.txt"

    def assert_matches_original(self, payload: bytes, chunk_size: int):
        self.path.write_bytes(payload)
        self.assertEqual(count_text(self.path, chunk_size), legacy_text_counts(self.path), msg=repr(payload))

    def test_edge_cases(self):
        cases = [b"", b"\n", b"\r", b"\r\n", b"a", b"a\n", b"a\nb", b"a\r\nb\r\n", b"\n\n\n", b"x\x0by\x85z", "one two".encode()]
        for payload in cases:
            for chunk_size in (1, 2, 3, 1024):
                with self.subTest(payload=payload, chunk_size=chunk_size):
                    self.assert_matches_original(payload, chunk_size)

    def test_invalid_utf8_is_ignored_like_before(self):
        for chunk_size in (1, 2, 5, 100):
            self.assert_matches_original(b"ok\xff\xfe\nbad \xc3\n\xe2\x82", chunk_size)  # truncated sequences too

    def test_random_inputs_with_tiny_chunks(self):
        rng = random.Random(20261019)
        for _ in range(400):
            text = "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(0, 60)))
            payload = text.encode("utf-8")
            if rng.random() < 0.3 and payload:  # chop a multi-byte sequence in half
                payload = payload[: rng.randint(0, len(payload))]
            self.assert_matches_original(payload, rng.randint(1, 9))


class PdfPagesTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = Path(self._dir.name) / "sample.pdf"

    def write(self, payload: bytes) -> Path:
        self.path.write_bytes(payload)
        return self.path

    def test_pages_root_is_not_counted_as_a_page(self):
        # A 3-page document: one "/Type /Pages" root and three "/Type /Page" leaves.
        pdf = b"%PDF-1.4\n1 0 obj<</Type /Pages /Count 3>>endobj\n" + b"2 0 obj<</Type /Page>>endobj\n" * 3
        self.assertEqual(count_pdf_pages(self.write(pdf)), 3)
        self.assertEqual(legacy_pdf_pages(self.path), 4)  # the old behaviour: root counted too (bug)

    def test_single_page_pdf(self):
        pdf = b"%PDF-1.4\n<</Type /Pages /Count 1>>\n<</Type /Page>>\n"
        self.assertEqual(count_pdf_pages(self.write(pdf)), 1)
        self.assertEqual(legacy_pdf_pages(self.path), 2)

    def test_compact_spelling_without_space(self):
        pdf = b"<</Type/Pages/Count 2>><</Type/Page>><</Type/Page>>"
        self.assertEqual(count_pdf_pages(self.write(pdf)), 2)
        self.assertEqual(legacy_pdf_pages(self.path), 1)  # old code could not see "/Type/Page"

    def test_minimum_is_one_and_empty_file_is_safe(self):
        self.assertEqual(count_pdf_pages(self.write(b"not really a pdf")), 1)
        self.assertEqual(count_pdf_pages(self.write(b"")), 1)

    def test_other_page_like_names_are_not_counted(self):
        self.assertEqual(count_pdf_pages(self.write(b"<</Type /PageLabels>> <</Type /Page>>")), 1)


class ExtractMetadataTest(unittest.TestCase):
    def test_keys_per_mime_type(self):
        with tempfile.TemporaryDirectory() as directory:
            text = Path(directory) / "a.txt"
            text.write_bytes(b"one\ntwo\n")
            self.assertEqual(
                extract_metadata(text, original_name="A.TXT", size=8, mime_type="text/plain"),
                {"extension": ".txt", "size_bytes": 8, "mime_type": "text/plain", "line_count": 2, "char_count": 8},
            )

            pdf = Path(directory) / "a.pdf"
            pdf.write_bytes(b"<</Type /Page>>")
            self.assertEqual(
                extract_metadata(pdf, original_name="a.pdf", size=15, mime_type="application/pdf"),
                {"extension": ".pdf", "size_bytes": 15, "mime_type": "application/pdf", "approx_page_count": 1},
            )

            other = Path(directory) / "a.bin"
            other.write_bytes(b"\x00")
            self.assertEqual(
                extract_metadata(other, original_name="a.bin", size=1, mime_type="image/png"),
                {"extension": ".bin", "size_bytes": 1, "mime_type": "image/png"},
            )


if __name__ == "__main__":
    unittest.main()
