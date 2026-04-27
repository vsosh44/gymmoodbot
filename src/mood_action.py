import asyncio
from datetime import datetime, time, timedelta, UTC
from zoneinfo import ZoneInfo
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import send_mood
from src.utils.database import Session
from src.types.enums import MoodType
from src.types.models import UserOrm, MoodLogOrm
from src.types.schemas import Mood


def next_random_time(start_hour, end_hour) -> datetime:
    zone = ZoneInfo("Europe/Moscow")
    now = datetime.now(zone)

    day = (now + timedelta(days=1)).date()

    start = datetime.combine(day, time(start_hour, 0), zone)
    end = datetime.combine(day, time(end_hour, 0), zone)

    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


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
                try:
                    time_now = datetime.now(UTC)
                    mood = Mood(
                        classname=user.classname,
                        type=MoodType.sunny,
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
                    print("[ERROR] process_users():", e)

                    user.next_mood_at = time_now + timedelta(minutes=15)


async def scheduler():
    while True:
        try:
            await process_users()
        except Exception as e:
            print("[ERROR] scheduler():", e)

        await asyncio.sleep(60)
