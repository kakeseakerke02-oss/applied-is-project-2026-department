"""Нақты HTTP сұраныстарымен тест. Іске қосу: python -m unittest discover -s tests -v"""

import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import sysconfig
from tempfile import TemporaryDirectory
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import sqlite3
from contextlib import closing

from app.database.db import make_engine
from seed import seed

ROOT = Path(__file__).resolve().parents[1]


class AssessmentAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(prefix="department_api_")
        db = Path(cls.directory.name) / "api.db"
        cls.db_path = db
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
        # Windows venv python.exe қайта бағыттаушысы қосымша процесс ашуы мүмкін.
        # Тест серверін нақты интерпретатормен ашып, venv пакеттерін сақтаймыз;
        # сонда terminate/wait базаны ұстап тұрған сервердің өзін тоқтатады.
        executable = sys.executable
        if os.name == "nt":
            executable = sys._base_executable
            env["PYTHONPATH"] = os.pathsep.join(filter(None, [sysconfig.get_path("purelib"), env.get("PYTHONPATH")]))
        cls.process = subprocess.Popen(
            [executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
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

    def request(self, path, data=None, method=None):
        req = Request(self.base + path,
                      data=None if data is None else json.dumps(data, ensure_ascii=False).encode(),
                      headers={"Content-Type": "application/json"}, method=method)
        try:
            response = urlopen(req, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            return response.status, json.loads(body) if body else None

    def test_get_routes_and_openapi(self):
        code, root = self.request("/")
        self.assertEqual(code, 200)
        self.assertEqual(root["labs"], [1, 2, 3, 4, 5])
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
        code, references = self.request("/reference-data")
        self.assertEqual(code, 200)
        self.assertEqual(len(references["disciplines"]), 3)
        self.assertEqual(len(references["teachers"]), 3)
        self.assertIn("label", references["teachers"][0])

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

    def test_patch_delete_and_filtering(self):
        sample = json.loads((ROOT / "docs/post_example.json").read_text(encoding="utf-8"))
        sample["title"] = "Арнайы Қазақша іздеу құралы 100%_SQL"
        status, original = self.request("/assessment-tools", sample)
        self.assertEqual(status, 201)
        tool_id = original["id"]
        path = f"/assessment-tools/{tool_id}"
        status, updated = self.request(path, {"content": "Өзгертілген мазмұн"}, "PATCH")
        self.assertEqual(status, 200)
        for key in original.keys() - {"content"}:
            self.assertEqual(updated[key], original[key])
        self.assertEqual(self.request(path)[1]["content"], "Өзгертілген мазмұн")
        for data in ({"title": " "}, {"title": None}, {"id": 500}, {"criteria": []},
                     {"criteria": [{"description": "score", "max_score": -1}]}):
            self.assertEqual(self.request(path, data, "PATCH")[0], 422)
        self.assertEqual(self.request(path, {"author_id": 999999}, "PATCH")[0], 404)
        self.assertEqual(self.request(path, {"discipline_id": 999999}, "PATCH")[0], 404)
        self.assertEqual(self.request(path, {"title": "SQL негіздері тесті"}, "PATCH")[0], 409)
        self.assertEqual(self.request(path)[1], updated)
        # Бірдей сипаттамамен қайта ауыстыру бірегейлік қатесіне әкелмеуі тиіс.
        replacements = sample["criteria"]
        replacements[0]["max_score"] = 35
        status, updated = self.request(path, {"criteria": replacements}, "PATCH")
        self.assertEqual(status, 200)
        self.assertEqual(updated["total_score"], "45.00")
        for params in ({"search": "қАЗАҚША", "min_score": 45, "max_score": 45},
                       {"search": "100%_SQL"},
                       {"search": "арнайы", "discipline_id": 1, "author_id": 1,
                        "tool_type": "Практикалық тапсырма"}):
            code, result = self.request("/assessment-tools?" + urlencode(params))
            self.assertEqual(code, 200)
            self.assertEqual([item["id"] for item in result], [tool_id])
        self.assertEqual(self.request("/assessment-tools?" + urlencode({"search": "' OR 1=1 --"}))[1], [])
        self.assertEqual(self.request("/assessment-tools?" + urlencode({"search": "%"}))[1][0]["id"], tool_id)
        self.assertEqual(self.request("/assessment-tools?min_score=50&max_score=10")[0], 422)
        self.assertEqual(self.request("/assessment-tools?min_score=-1")[0], 422)
        self.assertEqual(self.request("/assessment-tools?min_score=NaN")[0], 422)
        self.assertEqual(self.request("/assessment-tools?max_score=Infinity")[0], 422)
        self.assertEqual(self.request(path, method="DELETE"), (204, None))
        for method, data in (("GET", None), ("PATCH", {"title": "New"}), ("DELETE", None)):
            self.assertEqual(self.request(path, data, method)[0], 404)
        with closing(sqlite3.connect(self.db_path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM assessmenttool WHERE id=?", (tool_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM criterion WHERE assessment_tool_id=?", (tool_id,)).fetchone()[0], 0)

    def test_streamlit_user_flow(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest

        def button(app, label):
            return next(item for item in app.button if item.label == label)

        with patch.dict(os.environ, {"BACKEND_URL": self.base}):
            ui = AppTest.from_file(str(ROOT / "app/frontend/ui.py")).run(timeout=30)
            self.assertFalse(ui.exception)
            self.assertEqual(len(ui.metric), 3)
            ui.text_input[0].set_value("SQL").run(timeout=30)
            self.assertFalse(ui.exception)
            self.assertTrue(all("sql" in v.casefold() for v in ui.dataframe[0].value["Атауы"]))
            button(ui, "Сүзгілерді тазарту").click().run(timeout=30)
            self.assertEqual(ui.text_input[0].value, "")

            ui.radio[0].set_value("Құрал қосу").run(timeout=30)
            self.assertFalse(ui.exception)
            ui.text_input[0].set_value("Интерфейс арқылы тестілік құрал")
            ui.text_area[0].set_value("Қазақша интерфейс арқылы жасалған тапсырма.")
            button(ui, "Құралды қосу").click().run(timeout=30)
            self.assertFalse(ui.exception)
            found = self.request("/assessment-tools?" + urlencode({"search": "Интерфейс арқылы тестілік құрал"}))[1]
            self.assertEqual(len(found), 1)
            created_id = found[0]["id"]
            self.assertEqual(found[0]["total_score"], "30.00")
            self.assertEqual(ui.radio[0].value, "Бағалау құралдары")
            self.assertIn(created_id, list(ui.dataframe[0].value["№"]))
            self.assertEqual(ui.selectbox[-1].value, created_id)

            ui.radio[0].set_value("Құралды өзгерту").run(timeout=30)
            ui.selectbox[0].set_value(created_id).run(timeout=30)
            ui.text_input[0].set_value("Интерфейс арқылы жаңартылған құрал")
            button(ui, "Өзгерістерді сақтау").click().run(timeout=30)
            self.assertFalse(ui.exception)
            self.assertEqual(self.request(f"/assessment-tools/{created_id}")[1]["title"], "Интерфейс арқылы жаңартылған құрал")

            ui.radio[0].set_value("Құралды жою").run(timeout=30)
            ui.selectbox[0].set_value(created_id).run(timeout=30)
            self.assertTrue(button(ui, "Құралды жою").disabled)
            ui.checkbox[0].set_value(True).run(timeout=30)
            button(ui, "Құралды жою").click().run(timeout=30)
            self.assertFalse(ui.exception)
            self.assertEqual(self.request(f"/assessment-tools/{created_id}")[0], 404)
            ui.radio[0].set_value("Жоба туралы").run(timeout=30)
            self.assertFalse(ui.exception)
