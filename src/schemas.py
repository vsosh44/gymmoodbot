from datetime import datetime
from pydantic import BaseModel
from src.enums import MoodType


class User(BaseModel):
    tg_id: int
    tg_username: str
    expires_at: datetime
    classname: str
    mood_id: int


class Mood(BaseModel):
    operation_id: str = ""
    classname: str
    type: MoodType
    id: int
    time: datetime
