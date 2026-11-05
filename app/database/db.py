"""SQLite қосылымы, кестелерді құру және сессия өмірлік циклі."""

import os
from pathlib import Path

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.database import models  # Барлық модельдерді metadata ішінде тіркеу.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(PROJECT_ROOT / "database.db"))).resolve()


def make_engine(db_path: Path, echo: bool = True):
    engine = create_engine(
        f"sqlite:///{db_path.resolve().as_posix()}",
        echo=echo,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        # SQLite lower() әдепкіде кирилл әріптерін толық түрлендірмейді.
        connection.create_function("casefold", 1, lambda value: (value or "").casefold(), deterministic=True)
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = make_engine(DB_PATH)


def init_db(db_engine=None):
    SQLModel.metadata.create_all(engine if db_engine is None else db_engine)


def get_session():
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    init_db()
