"""Бағалау құралдарын оқу және критерийлерімен бірге жасау API-ы."""

from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database.db import get_session
from app.database.models import AssessmentTool, Criterion, Discipline, Teacher
from app.schemas import AssessmentToolCreate, AssessmentToolRead, AssessmentToolUpdate, CriterionRead

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


@router.get("", response_model=list[AssessmentToolRead], summary="Бағалау құралдарын алу, іздеу және сүзу")
def list_tools(
    session: SessionDep,
    search: Annotated[str | None, Query(max_length=200, description="Атауының бөлігі, әріп регистріне тәуелсіз")] = None,
    discipline_id: Annotated[int | None, Query(gt=0)] = None,
    author_id: Annotated[int | None, Query(gt=0)] = None,
    tool_type: Literal["Тест", "Емтихан", "Зертханалық жұмыс", "Практикалық тапсырма"] | None = None,
    min_score: Annotated[Decimal | None, Query(ge=0, allow_inf_nan=False, description="Жалпы максималды баллдың төменгі шегі")] = None,
    max_score: Annotated[Decimal | None, Query(ge=0, allow_inf_nan=False, description="Жалпы максималды баллдың жоғарғы шегі")] = None,
):
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(status_code=422, detail="min_score max_score мәнінен үлкен болмауы тиіс")
    statement = (select(AssessmentTool).options(selectinload(AssessmentTool.criteria))
                 .order_by(AssessmentTool.id))
    if search is not None and search.strip():
        statement = statement.where(func.casefold(AssessmentTool.title).contains(search.strip().casefold(), autoescape=True))
    for column, value in ((AssessmentTool.discipline_id, discipline_id),
                          (AssessmentTool.author_id, author_id), (AssessmentTool.tool_type, tool_type)):
        if value is not None:
            statement = statement.where(column == value)
    total = (select(func.coalesce(func.sum(Criterion.max_score), 0))
             .where(Criterion.assessment_tool_id == AssessmentTool.id).correlate(AssessmentTool).scalar_subquery())
    if min_score is not None:
        statement = statement.where(total >= min_score)
    if max_score is not None:
        statement = statement.where(total <= max_score)
    return [to_response(tool) for tool in session.exec(statement).all()]


@router.get("/{tool_id}", response_model=AssessmentToolRead, summary="Бағалау құралын ID арқылы алу")
def get_tool(tool_id: ToolId, session: SessionDep):
    tool = session.get(AssessmentTool, tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Бағалау құралы табылмады")
    return to_response(tool)


@router.patch("/{tool_id}", response_model=AssessmentToolRead, summary="Бағалау құралын ішінара өзгерту")
def update_tool(tool_id: ToolId, data: AssessmentToolUpdate, session: SessionDep):
    tool = session.get(AssessmentTool, tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Бағалау құралы табылмады")
    changes = data.model_dump(exclude_unset=True, exclude={"criteria"})
    if "discipline_id" in changes and session.get(Discipline, changes["discipline_id"]) is None:
        raise HTTPException(status_code=404, detail="Пән табылмады")
    if "author_id" in changes and session.get(Teacher, changes["author_id"]) is None:
        raise HTTPException(status_code=404, detail="Автор табылмады")
    try:
        tool.sqlmodel_update(changes)
        if "criteria" in data.model_fields_set:
            # Жіберілсе толық ауыстырылады; жіберілмесе ескі критерийлер сақталады.
            tool.criteria.clear()
            session.flush()  # Ескі бірегей сипаттамаларды жаңа INSERT алдында босату.
            tool.criteria = [Criterion(**criterion.model_dump()) for criterion in data.criteria]
        session.add(tool)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Өзгеріс деректердің бірегейлігіне немесе байланыстарына қайшы келеді") from None
    session.refresh(tool)
    return to_response(tool)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Бағалау құралын және оның критерийлерін жою")
def delete_tool(tool_id: ToolId, session: SessionDep):
    tool = session.get(AssessmentTool, tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="Бағалау құралы табылмады")
    try:
        session.delete(tool)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Байланысты деректерге байланысты жою орындалмады") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
