from aiogram.types import User as TgUser

from src.utils.config import settings
from src.types.schemas import User
from src.services import get_user


async def get_tg_user(tg_user: TgUser) -> User | None:
    tg_id = tg_user.id
    user = await get_user(tg_id)
    if user is None: return None
    return user


def admin_check(tg_user: TgUser) -> bool:
    return tg_user.id in settings.admin_users


def main_admin_check(tg_user: TgUser) -> bool:
    return tg_user.id == settings.main_admin
