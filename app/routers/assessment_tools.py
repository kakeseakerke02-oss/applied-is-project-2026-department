"""Бағалау құралдарын оқу және критерийлерімен бірге жасау API-ы."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database.db import get_session
from app.database.models import AssessmentTool, Criterion, Discipline, Teacher
from app.schemas import AssessmentToolCreate, AssessmentToolRead, CriterionRead

router = APIRouter(prefix="/assessment-tools", tags=["Бағалау құралдары"])
SessionDep = Annotated[Session, Depends(get_session)]
ToolId = Annotated[int, Path(gt=0, description="Бағалау құралының ID мәні")]


def to_response(tool: AssessmentTool) -> AssessmentToolRead:
    return AssessmentToolRead(
        id=tool.id, discipline_id=tool.discipline_id, author_id=tool.author_id,
        title=tool.title, tool_type=tool.tool_type, content=tool.content,
        created_at=tool.created_at,
        criteria=[CriterionRead.model_validate(c) for c in sorted(tool.criteria, key=lambda c: c.id)],
        total_score=tool.total_score(),
    )


@router.get("", response_model=list[AssessmentToolRead], summary="Барлық бағалау құралдарын алу")
def list_tools(session: SessionDep):
    statement = (select(AssessmentTool).options(selectinload(AssessmentTool.criteria))
                 .order_by(AssessmentTool.id))
    return [to_response(tool) for tool in session.exec(statement).all()]


@router.get("/{tool_id}", response_model=AssessmentToolRead, summary="Бағалау құралын ID арқылы алу")
def get_tool(tool_id: ToolId, session: SessionDep):
    tool = session.get(AssessmentTool, tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Бағалау құралы табылмады")
    return to_response(tool)


@router.post("", response_model=AssessmentToolRead, status_code=status.HTTP_201_CREATED,
             summary="Жаңа бағалау құралын критерийлерімен бірге жасау")
def create_tool(data: AssessmentToolCreate, session: SessionDep):
    if session.get(Discipline, data.discipline_id) is None:
        raise HTTPException(status_code=404, detail="Пән табылмады")
    if session.get(Teacher, data.author_id) is None:
        raise HTTPException(status_code=404, detail="Автор табылмады")

    # ID және жасалу уақыты кіріс схемасында жоқ: оларды сервер жасайды.
    tool = AssessmentTool(**data.model_dump(exclude={"criteria"}))
    tool.criteria = [Criterion(**criterion.model_dump()) for criterion in data.criteria]
    session.add(tool)
    try:
        session.commit()  # Құрал және барлық критерий бір транзакцияда сақталады.
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Деректер қақтығысы: осы пән мен авторда мұндай атаулы құрал бар немесе байланыс өзгерді",
        ) from None
    session.refresh(tool)
    return to_response(tool)
