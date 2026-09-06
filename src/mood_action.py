import asyncio
from datetime import datetime, time, timedelta, UTC
from zoneinfo import ZoneInfo
import random
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import send_mood
from src.utils.database import Session
from src.types.enums import MoodType
from src.types.models import UserOrm, MoodLogOrm
from src.types.schemas import Mood, User

logger = logging.getLogger(__name__)


def next_random_time(start_hour, end_hour, include_weekends: bool = False) -> datetime:
    zone = ZoneInfo("Europe/Moscow")
    now = datetime.now(zone)

    day = (now + timedelta(days=1)).date()

    while not include_weekends and day.weekday() in {5, 6}:
        day += timedelta(days=1)

    start = datetime.combine(day, time(start_hour, 0), zone)
    end = datetime.combine(day, time(end_hour, 0), zone)

    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


def resolve_random_mood_type() -> MoodType:
    return random.choice([
        MoodType.joy,
        MoodType.calm
    ])


def resolve_mood_type(mood_type: str) -> MoodType:
    try:
        selected_mood = MoodType(mood_type)
    except ValueError:
        logger.warning("resolve_mood_type(): invalid mood_type from database: %s. Fallback to random.", mood_type)
        selected_mood = MoodType.random

    if selected_mood == MoodType.random:
        return resolve_random_mood_type()

    return selected_mood


async def fetch_due_users(session: AsyncSession) -> list[UserOrm]:
    stmt = (
        select(UserOrm)
        .where(
            UserOrm.expires_at > datetime.now(UTC),
            UserOrm.next_mood_at <= datetime.now(UTC),
        )
        .with_for_update(skip_locked=True)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def process_users():
    async with Session() as session:
        async with session.begin():
            users = await fetch_due_users(session)

            for user in users:
                time_now = datetime.now(UTC)

                try:
                    mood = Mood(
                        type=resolve_mood_type(user.mood_type),
                        local_date=time_now.date(),
                    )

                    sent = await send_mood(User.model_validate(user, from_attributes=True), mood)
                    if not sent:
                        raise RuntimeError("Mood was not sent to API")

                    session.add(MoodLogOrm(
                        user_id=user.tg_id,
                        mood_time=time_now
                    ))

                    user.next_mood_at = next_random_time(7, 8, user.set_mood_on_weekends)

                except Exception as e:
                    logger.warning(
                        "process_users(): failed to process user %s. Retry later. Error: %s",
                        user.tg_id,
                        e,
                    )

                    user.next_mood_at = time_now + timedelta(minutes=15)


async def scheduler():
    while True:
        try:
            await process_users()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("scheduler(): process_users failed: %s", e)

        await asyncio.sleep(60)
