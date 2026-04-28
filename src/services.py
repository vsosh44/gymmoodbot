import logging

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.types.enums import MoodType
from src.types.schemas import User
from src.types.models import UserOrm
from src.utils.database import Session

logger = logging.getLogger(__name__)


async def get_user(tg_id: int) -> User | None:
    try:
        async with Session() as session:
            stmt = select(UserOrm).where(UserOrm.tg_id == tg_id)
            user = await session.scalar(stmt)

            if user is None:
                return None

            return User.model_validate(user, from_attributes=True)

    except ValidationError as e:
        logger.error("get_user(): invalid user data in database. tg_id: %s. Error: %s", tg_id, e)
        return None

    except SQLAlchemyError as e:
        logger.error("get_user(): database error. tg_id: %s. Error: %s", tg_id, e)
        return None

    except Exception as e:
        logger.exception("get_user(): unexpected error. tg_id: %s. Error: %s", tg_id, e)
        return None


async def get_users() -> list[User]:
    try:
        async with Session() as session:
            stmt = select(UserOrm)
            users = (await session.scalars(stmt)).all()

            result = []
            for user in users:
                try:
                    result.append(User.model_validate(user, from_attributes=True))
                except ValidationError as e:
                    logger.error("get_users(): skip invalid user %s. Error: %s", getattr(user, "tg_id", None), e)

            return result

    except SQLAlchemyError as e:
        logger.error("get_users(): database error: %s", e)
        return []

    except Exception as e:
        logger.exception("get_users(): unexpected error: %s", e)
        return []


async def add_user(user: User):
    async with Session() as session:
        data = user.model_dump()
        data["mood_type"] = user.mood_type.value

        session.add(UserOrm(**data))
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception("add_user(): failed to add user %s. Error: %s", user.tg_id, e)
            raise


async def update_user_mood_type(tg_id: int, mood_type: MoodType) -> bool:
    async with Session() as session:
        try:
            stmt = select(UserOrm).where(UserOrm.tg_id == tg_id)
            user = await session.scalar(stmt)

            if user is None:
                return False

            user.mood_type = mood_type.value
            await session.commit()

            return True

        except Exception as e:
            await session.rollback()
            logger.exception("update_user_mood_type(): failed to update user %s. Error: %s", tg_id, e)
            raise


async def update_user_tg_username(tg_id: int, tg_username: str | None) -> bool:
    try:
        async with Session() as session:
            stmt = select(UserOrm).where(UserOrm.tg_id == tg_id)
            user = await session.scalar(stmt)

            if user is None:
                logger.warning("update_user_tg_username(): user not found. tg_id: %s", tg_id)
                return False

            user.tg_username = tg_username

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.exception(
                    "update_user_tg_username(): failed to commit username update. tg_id: %s. username: %s. Error: %s",
                    tg_id,
                    tg_username,
                    e,
                )
                raise

            return True

    except SQLAlchemyError as e:
        logger.error(
            "update_user_tg_username(): database error. tg_id: %s. username: %s. Error: %s",
            tg_id,
            tg_username,
            e,
        )
        return False

    except Exception as e:
        logger.exception(
            "update_user_tg_username(): unexpected error. tg_id: %s. username: %s. Error: %s",
            tg_id,
            tg_username,
            e,
        )
        return False
