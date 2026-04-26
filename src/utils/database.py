from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.utils.config import settings

engine = create_async_engine(settings.database_url)
Session = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
