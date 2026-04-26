from datetime import datetime, UTC

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InaccessibleMessage, InlineKeyboardButton, InlineKeyboardMarkup

from src.utils.tg_check import get_tg_user, admin_check

router = Router()


@router.message(Command("start"))
async def message_start(message: Message):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    user = await get_tg_user(message.from_user)
    if user is None: return

    status = user.expires_at >= datetime.now(UTC)
    text = "GymMoodBot\n\n"
    if status:
        expires_delta = (user.expires_at - datetime.now(UTC)).total_seconds()
        days = int(expires_delta // (24 * 60 * 60))
        hours = int((expires_delta % (24 * 60 * 60)) // (60 * 60))
        text += f"Подписка закончится через {days} дн., {hours} ч."
    else:
        text += "Подписка неактивна"

    inline_keyboard = []
    if admin_check(message.from_user):
        inline_keyboard.append([InlineKeyboardButton(text="Админка", callback_data="admin")])
    inline_keyboard.append([InlineKeyboardButton(text="Кастомизация", callback_data="customize")])
    kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer(text, reply_markup=kb)
