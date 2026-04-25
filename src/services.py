from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.schemas import User
from src.models import UserOrm
from src.database import Session


async def get_user(tg_id: int) -> User | None:
    try:
        async with Session() as session:
            stmt = select(UserOrm).where(UserOrm.tg_id == tg_id)
            user = await session.scalar(stmt)

            if user is None:
                return None

            return User.model_validate(user, from_attributes=True)
    except (SQLAlchemyError, ValidationError) as exc:
        print("[ERROR] get_user() Error:", exc)
        return None


async def get_users() -> list[User]:
    try:
        async with Session() as session:
            stmt = select(UserOrm)
            users = (await session.scalars(stmt)).all()

            return [User.model_validate(user, from_attributes=True) for user in users]
    except (SQLAlchemyError, ValidationError) as exc:
        print("[ERROR] get_users() Error:", exc)
        return []


async def add_user(user: User) -> bool:
    async with Session() as session:
        session.add(UserOrm(**user.model_dump()))
        try:
            await session.commit()
            return True
        except IntegrityError as e:
            print("[ERROR] add_user() IntegrityError:", e)
            await session.rollback()
            return False
