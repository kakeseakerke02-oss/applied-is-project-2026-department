"""Контейнердің бірінші қосылуында демо базасын дайындап, Uvicorn іске қосу."""
import os
from app.database.db import DB_PATH, init_db
from seed import seed


def prepare_database():
    first_start = not DB_PATH.exists()
    init_db()
    if first_start:
        seed()
    # Бар volume ішіндегі деректерді қайта толтырмаймыз: пайдаланушы
    # жойған демо жазбалар контейнер қайта қосылғанда пайда болмауы тиіс.


if __name__ == "__main__":
    prepare_database()
    os.execvp("python", ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
