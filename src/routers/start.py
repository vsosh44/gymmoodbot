from datetime import datetime, UTC

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InaccessibleMessage, InlineKeyboardButton, InlineKeyboardMarkup

from src.utils.tg_check import get_tg_user, admin_check

router = Router()


async def get_start_menu(tg_user):
    user = await get_tg_user(tg_user)
    if user is None:
        return None, None

    status = user.expires_at >= datetime.now(UTC)
    text = "💚 <u><strong>GymMoodBot</strong></u> 💛\n\n"
    if status:
        expires_delta = (user.expires_at - datetime.now(UTC)).total_seconds()
        days = int(expires_delta // (24 * 60 * 60))
        hours = int((expires_delta % (24 * 60 * 60)) // (60 * 60))
        text += f"✅ Подписка закончится через: <code>{days} дн., {hours} ч</code>"
    else:
        text += "Подписка неактивна"

    inline_keyboard = []
    if admin_check(tg_user):
        inline_keyboard.append([InlineKeyboardButton(text="Админка 👑", callback_data="admin")])
    inline_keyboard.append([InlineKeyboardButton(text="Кастомизация ✏️", callback_data="customize")])
    kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    return text, kb


@router.message(Command("start"))
async def message_start(message: Message):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return

    text, kb = await get_start_menu(message.from_user)
    if text is None or kb is None: return

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "back_to_start")
async def callback_back_to_start(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return

    text, kb = await get_start_menu(callback.from_user)
    if text is None or kb is None: return

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
