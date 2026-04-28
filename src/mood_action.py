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
from src.types.schemas import Mood

logger = logging.getLogger(__name__)


def next_random_time(start_hour, end_hour) -> datetime:
    zone = ZoneInfo("Europe/Moscow")
    now = datetime.now(zone)

    day = (now + timedelta(days=1)).date()

    start = datetime.combine(day, time(start_hour, 0), zone)
    end = datetime.combine(day, time(end_hour, 0), zone)

    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


def resolve_mood_type(mood_type: str) -> MoodType:
    selected_mood = MoodType(mood_type)

    if selected_mood == MoodType.random:
        return random.choice([
            MoodType.sunny,
            MoodType.creative,
            MoodType.peaceful,
        ])

    return selected_mood


async def fetch_due_users(session: AsyncSession) -> list[UserOrm]:
    stmt = (
        select(UserOrm)
        .where(
            UserOrm.expires_at > datetime.now(UTC),
            UserOrm.next_mood_at <= datetime.now(),
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
                        classname=user.classname,
                        type=resolve_mood_type(user.mood_type),
                        id=user.mood_id,
                        time=time_now
                    )
                    await send_mood(mood)

                    session.add(MoodLogOrm(
                        user_id=user.tg_id,
                        mood_time=time_now
                    ))

                    user.next_mood_at = next_random_time(7, 8)
                except Exception as e:
                    logger.error("process_users(): %s", e)

                    user.next_mood_at = time_now + timedelta(minutes=15)


async def scheduler():
    while True:
        try:
            await process_users()
        except Exception as e:
            logger.error("scheduler(): %s", e)

        await asyncio.sleep(60)
