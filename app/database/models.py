"""Кафедраның бағалау құралдары қорының SQLModel модельдері."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class TeacherDisciplineLink(SQLModel, table=True):
    """Пән жүргізетін оқытушылар: құрама алғашқы кілті бар N:M байланыс."""

    teacher_id: int = Field(foreign_key="teacher.id", primary_key=True)
    discipline_id: int = Field(foreign_key="discipline.id", primary_key=True)


class Department(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=150)
    code: str = Field(unique=True, index=True, max_length=30)

    teachers: list["Teacher"] = Relationship(back_populates="department")
    disciplines: list["Discipline"] = Relationship(back_populates="department")


class Teacher(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    department_id: int = Field(foreign_key="department.id", index=True)
    full_name: str = Field(max_length=150)
    email: str = Field(unique=True, index=True, max_length=150)

    department: Department = Relationship(back_populates="teachers")
    authored_tools: list["AssessmentTool"] = Relationship(back_populates="author")
    disciplines: list["Discipline"] = Relationship(
        back_populates="teachers", link_model=TeacherDisciplineLink
    )


class Discipline(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    department_id: int = Field(foreign_key="department.id", index=True)
    code: str = Field(unique=True, index=True, max_length=30)
    name: str = Field(max_length=200)

    department: Department = Relationship(back_populates="disciplines")
    assessment_tools: list["AssessmentTool"] = Relationship(back_populates="discipline")
    teachers: list[Teacher] = Relationship(
        back_populates="disciplines", link_model=TeacherDisciplineLink
    )


class AssessmentTool(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("discipline_id", "author_id", "title", name="uq_tool_author_discipline_title"),
        CheckConstraint("length(trim(title)) > 0", name="ck_tool_title"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    discipline_id: int = Field(foreign_key="discipline.id", index=True)
    author_id: int = Field(foreign_key="teacher.id", index=True)
    title: str = Field(max_length=200)
    tool_type: str = Field(max_length=30)
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    discipline: Discipline = Relationship(back_populates="assessment_tools")
    author: Teacher = Relationship(back_populates="authored_tools")
    criteria: list["Criterion"] = Relationship(
        back_populates="assessment_tool", cascade_delete=True
    )

    def total_score(self) -> Decimal:
        """Жүктелген критерийлердің максималды балдарын қосу."""
        return sum((criterion.max_score for criterion in self.criteria), Decimal("0.00"))


class Criterion(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("max_score > 0", name="ck_criterion_positive_score"),
        CheckConstraint("length(trim(description)) > 0", name="ck_criterion_description"),
        UniqueConstraint("assessment_tool_id", "description", name="uq_tool_criterion"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_tool_id: int = Field(foreign_key="assessmenttool.id", index=True)
    description: str
    max_score: Decimal = Field(gt=0, max_digits=6, decimal_places=2)

    assessment_tool: AssessmentTool = Relationship(back_populates="criteria")
