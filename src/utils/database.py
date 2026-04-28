from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import asyncio
import logging

from sqlalchemy.orm import DeclarativeBase

from src.utils.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def create_all():
    retry_count = 5
    retry_delay = 2

    for attempt in range(1, retry_count + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            return

        except Exception as e:
            logger.exception(
                "create_all(): database initialization failed. Attempt %s/%s. Error: %s",
                attempt,
                retry_count,
                e,
            )

            if attempt == retry_count:
                logger.error("create_all(): database initialization failed after all attempts")
                return

            await asyncio.sleep(retry_delay * attempt)
