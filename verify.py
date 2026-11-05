"""Қолданыстағы базаға жазбай, бөлек уақытша базада модельдерді тексеру."""

from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import func, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database.db import make_engine
from app.database.models import (
    Department, Teacher, Discipline, AssessmentTool, Criterion, TeacherDisciplineLink,
)
from seed import seed

MODELS = (Department, Teacher, Discipline, AssessmentTool, Criterion, TeacherDisciplineLink)


def counts(engine):
    with Session(engine) as session:
        return {m.__tablename__: session.exec(select(func.count()).select_from(m)).one()
                for m in MODELS}


def rejects(engine, obj):
    with Session(engine) as session:
        session.add(obj)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            return
        session.rollback()
        raise AssertionError("Invalid row was accepted")


def main():
    with TemporaryDirectory(prefix="department_db_") as directory:
        engine = make_engine(Path(directory) / "test.db", echo=False)
        try:
            seed(engine)
            before = counts(engine)
            assert before == {"department": 3, "teacher": 3, "discipline": 3,
                              "assessmenttool": 5, "criterion": 5, "teacherdisciplinelink": 5}
            seed(engine)
            assert counts(engine) == before
            assert len(inspect(engine).get_table_names()) == 6
            with Session(engine) as session:
                teacher = session.exec(select(Teacher).where(Teacher.email == "a.serik@example.com")).one()
                discipline = session.exec(select(Discipline).where(Discipline.code == "DB101")).one()
                assert len(teacher.disciplines) == 2 and len(discipline.teachers) == 2
                assert teacher in teacher.department.teachers
                assert discipline in discipline.department.disciplines
                tool = session.exec(select(AssessmentTool).where(AssessmentTool.title == "SQL негіздері тесті")).one()
                assert tool.author.email == teacher.email and tool.discipline.code == "DB101"
                assert tool in tool.author.authored_tools and tool in discipline.assessment_tools
                assert tool.criteria[0].assessment_tool.id == tool.id
                assert tool.total_score() == Decimal("20.00")
                teacher_id, discipline_id, tool_id = teacher.id, discipline.id, tool.id
                assert session.exec(text("PRAGMA foreign_key_check")).all() == []
            rejects(engine, Teacher(department_id=-1, full_name="Invalid", email="bad@example.com"))
            rejects(engine, Department(name="Duplicate", code="IS"))
            rejects(engine, Teacher(department_id=1, full_name="Duplicate", email="a.serik@example.com"))
            rejects(engine, TeacherDisciplineLink(teacher_id=teacher_id, discipline_id=discipline_id))
            for score in ("0", "-1"):
                rejects(engine, Criterion(assessment_tool_id=tool_id, description="Invalid score", max_score=Decimal(score)))
            rejects(engine, Criterion(assessment_tool_id=-1, description="Invalid FK", max_score=Decimal("1")))
            # Композиция: құрал жойылса, оның критерийлері ORM арқылы бірге жойылады.
            with Session(engine) as session:
                tool = session.get(AssessmentTool, tool_id)
                session.delete(tool)
                session.commit()
                assert not session.exec(select(Criterion).where(Criterion.assessment_tool_id == tool_id)).all()
            print("PASS: 6 tables; one-to-many; many-to-many; Decimal scores; repeat seed")
            print("PASS: foreign keys; uniqueness; composite PK; positive score; cascade delete")
            print(before)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
