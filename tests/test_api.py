"""Нақты HTTP сұраныстарымен тест. Іске қосу: python -m unittest discover -s tests -v"""

import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.database.db import make_engine
from seed import seed

ROOT = Path(__file__).resolve().parents[1]


class AssessmentAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(prefix="department_api_")
        db = Path(cls.directory.name) / "api.db"
        engine = make_engine(db, echo=False)
        try:
            seed(engine)
        finally:
            engine.dispose()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        cls.log = (Path(cls.directory.name) / "server.log").open("w+", encoding="utf-8")
        env = dict(os.environ, DATABASE_PATH=str(db), PYTHONIOENCODING="utf-8")
        cls.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=cls.log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                with urlopen(cls.base + "/", timeout=1) as response:
                    if response.status == 200:
                        return
            except (URLError, TimeoutError):
                if cls.process.poll() is not None:
                    break
                time.sleep(0.1)
        cls.process.terminate()
        cls.process.wait(timeout=10)
        cls.log.seek(0)
        logs = cls.log.read()
        cls.log.close()
        cls.directory.cleanup()
        raise RuntimeError("Test server did not start:\n" + logs)

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=10)
        cls.log.close()
        cls.directory.cleanup()

    def request(self, path, data=None):
        req = Request(self.base + path,
                      data=None if data is None else json.dumps(data, ensure_ascii=False).encode(),
                      headers={"Content-Type": "application/json"})
        try:
            response = urlopen(req, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_get_routes_and_openapi(self):
        code, root = self.request("/")
        self.assertEqual(code, 200)
        self.assertEqual(root["labs"], [1, 2, 3])
        code, tools = self.request("/assessment-tools")
        self.assertEqual(code, 200)
        self.assertGreaterEqual(len(tools), 5)
        code, tool = self.request("/assessment-tools/1")
        self.assertEqual(code, 200)
        self.assertEqual(tool["total_score"], "20.00")
        self.assertEqual(self.request("/assessment-tools/999999")[0], 404)
        self.assertEqual(self.request("/assessment-tools/0")[0], 422)
        code, spec = self.request("/openapi.json")
        self.assertEqual(code, 200)
        self.assertIn("post", spec["paths"]["/assessment-tools"])
        self.assertNotIn("id", spec["components"]["schemas"]["AssessmentToolCreate"]["properties"])

    def test_post_atomic_creation_validation_and_conflicts(self):
        sample = json.loads((ROOT / "docs/post_example.json").read_text(encoding="utf-8"))
        baseline = len(self.request("/assessment-tools")[1])
        invalid = []
        for key, value in [("title", "   "), ("content", " "), ("id", 123),
                           ("created_at", "2000-01-01T00:00:00"), ("discipline_id", 0),
                           ("tool_type", "unknown"), ("author_id", True), ("criteria", [])]:
            data = copy.deepcopy(sample)
            data[key] = value
            invalid.append(data)
        for score in (-1, 0, "NaN", "1.001"):
            data = copy.deepcopy(sample)
            data["criteria"][0]["max_score"] = score
            invalid.append(data)
        data = copy.deepcopy(sample)
        data["criteria"][1]["description"] = data["criteria"][0]["description"]
        invalid.append(data)
        for index, data in enumerate(invalid):
            with self.subTest(invalid_payload=index):
                self.assertEqual(self.request("/assessment-tools", data)[0], 422)
        for key in ("discipline_id", "author_id"):
            data = copy.deepcopy(sample)
            data[key] = 999999
            self.assertEqual(self.request("/assessment-tools", data)[0], 404)
        self.assertEqual(len(self.request("/assessment-tools")[1]), baseline)
        code, created = self.request("/assessment-tools", sample)
        self.assertEqual(code, 201)
        self.assertEqual(len(created["criteria"]), 2)
        self.assertEqual(created["total_score"], "30.00")
        self.assertIn("created_at", created)
        self.assertEqual(self.request(f"/assessment-tools/{created['id']}")[1], created)
        self.assertEqual(self.request("/assessment-tools", sample)[0], 409)
        self.assertEqual(len(self.request("/assessment-tools")[1]), baseline + 1)
