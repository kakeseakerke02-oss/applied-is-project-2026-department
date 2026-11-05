"""Streamlit интерфейсінің FastAPI клиенті."""
import os
import requests

class APIError(Exception):
    pass

def api_request(method, path, *, params=None, data=None):
    base = os.getenv("BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
    try:
        response = requests.request(method, base + path, params=params, json=data, timeout=10)
    except requests.RequestException as exc:
        raise APIError("Серверге қосылу мүмкін болмады. Сервердің іске қосылғанын тексеріңіз.") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Сұраныс орындалмады")
        except ValueError:
            detail = "Сервер сұранысты орындай алмады"
        if isinstance(detail, list):
            fields = {"title": "Атауы", "content": "Мазмұны", "criteria": "Критерийлер",
                      "description": "Сипаттама", "max_score": "Максималды балл",
                      "discipline_id": "Пән", "author_id": "Автор", "tool_type": "Құрал түрі"}
            detail = "; ".join(" → ".join(fields.get(str(p), str(p)) for p in e.get("loc", [])
                                        if p not in ("body", "query")) + ": " + e.get("msg", "Мәнін тексеріңіз") for e in detail)
        raise APIError(f"{detail} ({response.status_code})")
    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise APIError("Серверден дұрыс жауап алынбады.") from exc
