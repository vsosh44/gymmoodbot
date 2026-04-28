import logging
from aiogram.types import User as TgUser

from src.utils.config import settings
from src.types.schemas import User
from src.services import get_user, update_user_tg_username

logger = logging.getLogger(__name__)


async def get_tg_user(tg_user: TgUser) -> User | None:
    tg_id = tg_user.id
    try:
        user = await get_user(tg_id)
    except Exception as e:
        logger.error("database get_user() error: %s", e)
        return None

    if user is None:
        return None

    try:
        await update_user_tg_username(tg_id, tg_user.username)
    except Exception as e:
        logger.exception(
            "get_tg_user(): failed to update tg_username. tg_id: %s. username: %s. Error: %s",
            tg_id,
            tg_user.username,
            e,
        )

    return user


def admin_check(tg_user: TgUser) -> bool:
    return tg_user.id in settings.admin_users


def main_admin_check(tg_user: TgUser) -> bool:
    return tg_user.id == settings.main_admin
