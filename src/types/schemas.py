from datetime import datetime, date
from pydantic import BaseModel
from src.types.enums import MoodType


class User(BaseModel):
    tg_id: int
    tg_username: str | None = None
    expires_at: datetime
    classname: str
    mood_id: int
    password: str
    mood_type: MoodType = MoodType.random
    next_mood_at: datetime
    set_mood_on_weekends: bool = False


class Mood(BaseModel):
    student_id: str = ""
    classname: str = ""
    profile: str = ""
    type: MoodType
    id: str = ""
    score: int = 0
    created_at: datetime = datetime(2000, 1,1)
    local_date: date
