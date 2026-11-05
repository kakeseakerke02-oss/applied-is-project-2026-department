"""Формада пән мен авторды атауы арқылы таңдау үшін анықтамалықтар."""
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database.db import get_session
from app.database.models import Discipline, Teacher

class NamedReference(BaseModel):
    id: int
    label: str

class ReferenceData(BaseModel):
    disciplines: list[NamedReference]
    teachers: list[NamedReference]

router = APIRouter(tags=["Анықтамалықтар"])

@router.get("/reference-data", response_model=ReferenceData, summary="Пәндер мен оқытушыларды алу")
def reference_data(session: Annotated[Session, Depends(get_session)]):
    disciplines = session.exec(select(Discipline).order_by(Discipline.id)).all()
    teachers = session.exec(select(Teacher).order_by(Teacher.id)).all()
    return ReferenceData(
        disciplines=[NamedReference(id=i.id, label=f"{i.code} — {i.name}") for i in disciplines],
        teachers=[NamedReference(id=i.id, label=i.full_name) for i in teachers],
    )
