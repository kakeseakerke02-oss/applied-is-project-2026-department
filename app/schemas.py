"""API сұранысы мен жауабы үшін ORM кестелерінен бөлек схемалар."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CriterionCreate(InputModel):
    description: str = Field(min_length=1, max_length=2000)
    max_score: Decimal = Field(gt=0, max_digits=6, decimal_places=2)


class AssessmentToolCreate(InputModel):
    discipline_id: int = Field(gt=0, strict=True)
    author_id: int = Field(gt=0, strict=True)
    title: str = Field(min_length=1, max_length=200)
    tool_type: Literal["Тест", "Емтихан", "Зертханалық жұмыс", "Практикалық тапсырма"]
    content: str = Field(min_length=1, max_length=20000)
    criteria: list[CriterionCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_criteria(self):
        descriptions = [criterion.description for criterion in self.criteria]
        if len(descriptions) != len(set(descriptions)):
            raise ValueError("Бір құралда критерий сипаттамалары қайталанбауы тиіс")
        return self


class CriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    description: str
    max_score: Decimal


class AssessmentToolRead(BaseModel):
    id: int
    discipline_id: int
    author_id: int
    title: str
    tool_type: str
    content: str
    created_at: datetime
    criteria: list[CriterionRead]
    total_score: Decimal
