from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from src.utils.database import Base


class UserOrm(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    classname: Mapped[str]
    mood_id: Mapped[int]
    mood_type: Mapped[str] = mapped_column(String, default="random")
    next_mood_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MoodLogOrm(Base):
    __tablename__ = "mood_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tg_id"))
    mood_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
