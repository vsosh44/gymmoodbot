import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.types import ErrorEvent

from src.utils.database import create_all
from src.mood_action import scheduler
from src.utils.config import settings
from src.routers import bot_routers

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

if settings.proxy:
    session = AiohttpSession(proxy="socks5://@127.0.0.1:10808")
else:
    session = None
bot = Bot(token=settings.bot_token, session=session)
dp = Dispatcher()


@dp.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    exception = event.exception

    if isinstance(exception, TelegramRetryAfter):
        logger.warning(
            "Telegram flood control. Retry after %s seconds",
            exception.retry_after,
        )
        return True

    if isinstance(exception, TelegramForbiddenError):
        logger.warning("Telegram forbidden error: %s", exception)
        return True

    if isinstance(exception, TelegramBadRequest):
        logger.warning("Telegram bad request: %s", exception)
        return True

    if isinstance(exception, TelegramNetworkError):
        logger.warning("Telegram network error: %s", exception)
        return True

    if isinstance(exception, TelegramAPIError):
        logger.warning("Telegram API error: %s", exception)
        return True

    logger.exception("Unhandled error: %s", exception)
    return True


async def main():
    await create_all()
    asyncio.create_task(scheduler())
    dp.include_routers(*bot_routers)
    await dp.start_polling(bot)


asyncio.run(main())
