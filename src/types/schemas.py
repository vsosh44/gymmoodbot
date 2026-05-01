from datetime import datetime
from pydantic import BaseModel
from src.types.enums import MoodType


class User(BaseModel):
    tg_id: int
    expires_at: datetime
    classname: str
    mood_id: int
    mood_type: MoodType = MoodType.random
    next_mood_at: datetime
    set_mood_on_weekends: bool = False


class Mood(BaseModel):
    operation_id: str = ""
    classname: str
    type: MoodType
    id: int
    time: datetime
