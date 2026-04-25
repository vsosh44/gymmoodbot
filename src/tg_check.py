from aiogram.types import Message, InaccessibleMessage
from aiogram.types import User as TgUser

from src.schemas import User
from src.services import get_user


async def get_tg_user(tg_user: TgUser) -> User | None:
    tg_id = tg_user.id
    user = await get_user(tg_id)
    if user is None: return None
    return user
