import asyncio
import io
import tempfile
import unittest
from pathlib import Path

from src.core.config import DEFAULT_CORS_ORIGINS, DEFAULT_REDIS_URL, load_settings
from src.file_storage.local import LocalFileStorage
from src.services.naming import fit_name, safe_suffix

_DB_ENV = {
    "POSTGRES_USER": "app",
    "POSTGRES_PASSWORD": "secret",
    "POSTGRES_HOST": "backend-db",
    "PGPORT": "5433",
    "POSTGRES_DB": "files",
}


class NamingTest(unittest.TestCase):
    def test_safe_suffix(self):
        self.assertEqual(safe_suffix("report.final.pdf"), ".pdf")
        self.assertEqual(safe_suffix("noext"), "")
        self.assertEqual(safe_suffix(None), "")
        self.assertEqual(safe_suffix("x." + "a" * 40), "")

    def test_fit_name_keeps_the_extension(self):
        long_name = "a" * 300 + ".exe"
        fitted = fit_name(long_name)
        self.assertEqual(len(fitted), 255)
        self.assertTrue(fitted.endswith(".exe"))  # otherwise a long ".exe" would scan as clean

    def test_fit_name_leaves_short_names_alone(self):
        self.assertEqual(fit_name("short.txt"), "short.txt")
        self.assertEqual(fit_name("a" * 255), "a" * 255)
        self.assertEqual(len(fit_name("x" * 400)), 255)


class ConfigTest(unittest.TestCase):
    def test_database_url_is_built_from_the_existing_variables(self):
        settings = load_settings(_DB_ENV)
        self.assertEqual(settings.database_url, "postgresql+asyncpg://app:secret@backend-db:5433/files")
        self.assertEqual(settings.redis_url, DEFAULT_REDIS_URL)
        self.assertEqual(settings.cors_origins, DEFAULT_CORS_ORIGINS)
        self.assertEqual(settings.storage_dir.parts[-2:], ("storage", "files"))

    def test_credentials_are_url_encoded(self):
        settings = load_settings({**_DB_ENV, "POSTGRES_PASSWORD": "p@ss/w:rd#1"})
        self.assertIn(":p%40ss%2Fw%3Ard%231@", settings.database_url)

    def test_missing_variables_fail_fast_with_names(self):
        env = {k: v for k, v in _DB_ENV.items() if k not in ("PGPORT", "POSTGRES_DB")}
        with self.assertRaises(RuntimeError) as caught:
            load_settings(env)
        self.assertIn("PGPORT", str(caught.exception))
        self.assertIn("POSTGRES_DB", str(caught.exception))

    def test_overrides(self):
        settings = load_settings(
            {
                "DATABASE_URL": "postgresql+asyncpg://u:p@h/db",
                "REDIS_URL": "redis://r:6379/5",
                "STORAGE_DIR": "/data/files",
                "CORS_ORIGINS": "https://a.example, https://b.example ,",
            }
        )
        self.assertEqual(settings.database_url, "postgresql+asyncpg://u:p@h/db")
        self.assertEqual(settings.redis_url, "redis://r:6379/5")
        self.assertEqual(settings.storage_dir, Path("/data/files"))
        self.assertEqual(settings.cors_origins, ("https://a.example", "https://b.example"))


class LocalStorageTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.storage = LocalFileStorage(Path(self._dir.name) / "nested" / "files")

    async def test_save_returns_size_and_roundtrips(self):
        payload = b"x" * (3 * 1024 * 1024 + 17)  # spans several copy chunks
        written = await self.storage.save("a.bin", io.BytesIO(payload))
        self.assertEqual(written, len(payload))
        self.assertTrue(await self.storage.exists("a.bin"))
        self.assertEqual(self.storage.local_path("a.bin").read_bytes(), payload)

    async def test_empty_source_reports_zero(self):
        self.assertEqual(await self.storage.save("empty.bin", io.BytesIO(b"")), 0)

    async def test_delete_is_idempotent(self):
        await self.storage.save("a.bin", io.BytesIO(b"1"))
        await self.storage.delete("a.bin")
        await self.storage.delete("a.bin")
        self.assertFalse(await self.storage.exists("a.bin"))

    async def test_failed_write_leaves_no_partial_file(self):
        class Exploding(io.RawIOBase):
            calls = 0

            def readable(self):
                return True

            def readinto(self, buffer):
                Exploding.calls += 1
                if Exploding.calls > 1:
                    raise OSError("disk went away")
                buffer[:4] = b"data"
                return 4

        with self.assertRaises(OSError):
            await self.storage.save("broken.bin", io.BufferedReader(Exploding()))
        self.assertFalse(await self.storage.exists("broken.bin"))

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.storage.local_path("../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
