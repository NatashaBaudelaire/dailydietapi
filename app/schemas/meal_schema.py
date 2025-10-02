from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class MealBase(BaseModel):
    name: str
    description: str
    datetime: datetime
    is_on_diet: bool
    category: Optional[str] = None
    calories: Optional[int] = None
    protein_grams: Optional[float] = None
    carbohydrates_grams: Optional[float] = None
    fats_grams: Optional[float] = None
    image_url: Optional[str] = None

class MealCreateSchema(MealBase):
    pass

class MealUpdateSchema(BaseModel):
    name: Optional[str]
    description: Optional[str]
    datetime: Optional[datetime]
    is_on_diet: Optional[bool]
    category: Optional[str]
    calories: Optional[int]
    protein_grams: Optional[float]
    carbohydrates_grams: Optional[float]
    fats_grams: Optional[float]