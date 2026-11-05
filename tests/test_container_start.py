"""Контейнердің бастапқы базасы және қайта қосылуда деректерді сақтау."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContainerStartTest(unittest.TestCase):
    def test_initial_seed_and_restart_preserve_changes(self):
        with TemporaryDirectory(prefix="department_container_") as directory:
            db = Path(directory) / "database.db"
            env = dict(os.environ, DATABASE_PATH=str(db), PYTHONIOENCODING="utf-8")

            def prepare():
                result = subprocess.run(
                    [sys.executable, "-c", "from app.container_start import prepare_database; prepare_database()"],
                    cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=45,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            prepare()
            with closing(sqlite3.connect(db)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM assessmenttool").fetchone()[0], 5)
                connection.execute("UPDATE assessmenttool SET title=? WHERE id=1", ("Сақталған өзгеріс",))
                connection.execute("DELETE FROM criterion WHERE assessment_tool_id=5")
                connection.execute("DELETE FROM assessmenttool WHERE id=5")
                connection.commit()
            prepare()
            with closing(sqlite3.connect(db)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM assessmenttool").fetchone()[0], 4)
                self.assertEqual(connection.execute("SELECT title FROM assessmenttool WHERE id=1").fetchone()[0], "Сақталған өзгеріс")
