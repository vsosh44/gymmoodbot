from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.types.enums import MoodType
from src.types.schemas import User
from src.types.models import UserOrm
from src.utils.database import Session


async def get_user(tg_id: int) -> User | None:
    async with Session() as session:
        stmt = select(UserOrm).where(UserOrm.tg_id == tg_id)
        user = await session.scalar(stmt)

        if user is None:
            return None

        return User.model_validate(user, from_attributes=True)


async def get_users() -> list[User]:
    async with Session() as session:
        stmt = select(UserOrm)
        users = (await session.scalars(stmt)).all()

        return [User.model_validate(user, from_attributes=True) for user in users]


async def add_user(user: User):
    async with Session() as session:
        data = user.model_dump()
        data["mood_type"] = user.mood_type.value

        session.add(UserOrm(**data))
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def update_user_mood_type(tg_id: int, mood_type: MoodType) -> bool:
    async with Session() as session:
        stmt = select(UserOrm).where(UserOrm.tg_id == tg_id)
        user = await session.scalar(stmt)

        if user is None:
            return False

        user.mood_type = mood_type.value

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        return True
