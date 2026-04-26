from datetime import datetime, UTC

from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, InlineKeyboardButton, InlineKeyboardMarkup

from src.services import get_users
from src.utils.tg_check import admin_check, get_tg_user

router = Router()


async def get_admin_panel():
    all_users = await get_users()
    text = "Админ панель\n\n"
    text += "Статистика:\n"
    text += f"Пользователей: {len(all_users)}\n"
    text += f"Активных пользователей: {len([0 for user in all_users if user.expires_at > datetime.now(UTC)])}\n"

    inline_keyboard = [
        [InlineKeyboardButton(text="Добавить пользователя", callback_data="add_user"),
         InlineKeyboardButton(text="Продлить пользователя", callback_data="renew_user")],
        [InlineKeyboardButton(text="Забанить пользователя", callback_data="ban_user")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    return text, kb


@router.callback_query(F.data == "admin")
async def callback_admin(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return
    if not admin_check(callback.from_user): return
    user = await get_tg_user(callback.from_user)
    if user is None: return

    text, kb = await get_admin_panel()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
