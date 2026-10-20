"""Orchestration tests for ProcessingPipeline with in-memory fakes (no database, no Celery).

Skipped when SQLAlchemy is not installed (the pipeline imports ``StaleDataError`` from it).
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy.orm.exc import StaleDataError

    from src.file_storage.local import LocalFileStorage
    from src.services.processing.pipeline import METADATA_FAILURE_DETAILS, ProcessingPipeline


def make_file(**overrides):
    values = {
        "id": "file-1",
        "original_name": "notes.txt",
        "stored_name": "file-1.txt",
        "size": 8,
        "mime_type": "text/plain",
        "processing_status": "uploaded",
        "scan_status": None,
        "scan_details": None,
        "requires_attention": False,
        "metadata_json": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeFiles:
    def __init__(self, file):
        self._file = file

    async def get(self, file_id):
        return self._file if self._file is not None and self._file.id == file_id else None


class FakeAlerts:
    def __init__(self):
        self.added = []

    def add(self, file_id, level, message):
        self.added.append((file_id, level, message))


class FakeSession:
    def __init__(self, file, fail_commit_number=None):
        self._file = file
        self._fail_commit_number = fail_commit_number
        self.commit_snapshots = []
        self.rolled_back = False

    async def commit(self):
        number = len(self.commit_snapshots) + 1
        self.commit_snapshots.append(self._file.processing_status)
        if number == self._fail_commit_number:
            raise StaleDataError("row was deleted")

    async def rollback(self):
        self.rolled_back = True


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy is not installed")
class PipelineTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.storage = LocalFileStorage(Path(self._dir.name))
        self.alerts = FakeAlerts()

    def pipeline(self, file, **session_kwargs):
        self.session = FakeSession(file, **session_kwargs)
        return ProcessingPipeline(
            session=self.session, files=FakeFiles(file), alerts=self.alerts, storage=self.storage
        )

    def store(self, name, payload: bytes):
        (self.storage.local_path(name)).write_bytes(payload)

    async def test_clean_text_file(self):
        file = make_file()
        self.store("file-1.txt", b"one\ntwo\n")

        await self.pipeline(file).run("file-1")

        self.assertEqual(file.processing_status, "processed")
        self.assertEqual((file.scan_status, file.scan_details, file.requires_attention), ("clean", "no threats found", False))
        self.assertEqual(
            file.metadata_json,
            {"extension": ".txt", "size_bytes": 8, "mime_type": "text/plain", "line_count": 2, "char_count": 8},
        )
        self.assertEqual(self.alerts.added, [("file-1", "info", "File processed successfully")])
        # Two commits; the first one makes the intermediate "processing" state visible.
        self.assertEqual(self.session.commit_snapshots, ["processing", "processed"])

    async def test_suspicious_file_raises_a_warning(self):
        file = make_file(original_name="run.exe", stored_name="file-1.exe", mime_type="application/octet-stream")
        self.store("file-1.exe", b"MZ")

        await self.pipeline(file).run("file-1")

        self.assertEqual(file.processing_status, "processed")
        self.assertEqual(file.scan_status, "suspicious")
        self.assertEqual(self.alerts.added, [("file-1", "warning", "File requires attention: suspicious extension .exe")])

    async def test_missing_stored_file_fails_with_a_critical_alert(self):
        file = make_file()  # nothing was written to the storage

        await self.pipeline(file).run("file-1")

        self.assertEqual(file.processing_status, "failed")
        self.assertEqual(file.scan_details, METADATA_FAILURE_DETAILS)
        self.assertEqual(file.scan_status, "clean")  # the scan result itself is kept, as before
        self.assertIsNone(file.metadata_json)
        self.assertEqual(self.alerts.added, [("file-1", "critical", "File processing failed")])

    async def test_unknown_file_is_ignored(self):
        file = make_file()
        pipeline = self.pipeline(file)
        await pipeline.run("does-not-exist")
        self.assertEqual(self.session.commit_snapshots, [])
        self.assertEqual(self.alerts.added, [])

    async def test_file_deleted_mid_processing_is_not_an_error(self):
        file = make_file()
        self.store("file-1.txt", b"x")

        await self.pipeline(file, fail_commit_number=2).run("file-1")  # must not raise

        self.assertTrue(self.session.rolled_back)


if __name__ == "__main__":
    unittest.main()
