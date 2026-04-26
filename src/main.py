import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from src.utils.database import create_all
from src.mood_action import scheduler
from src.utils.config import settings
from src.routers import bot_routers

session = AiohttpSession(proxy="socks5://@127.0.0.1:10808")
bot = Bot(token=settings.bot_token, session=session)
dp = Dispatcher()


async def main():
    await create_all()
    asyncio.create_task(scheduler())
    dp.include_routers(*bot_routers)
    await dp.start_polling(bot)


asyncio.run(main())
