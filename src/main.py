import asyncio
import os
from datetime import datetime, date

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InaccessibleMessage
from aiogram import F

from src.database import create_all
from src.enums import MoodType
from src.httpclient import http_client
from src.api import get_moods, send_mood
from src.mood_action import scheduler
from src.schemas import Mood
from src.services import get_user, get_users
from src.config import settings
from src.tg_check import get_tg_user

#session = AiohttpSession(proxy="socks5://@127.0.0.1:10808")
bot = Bot(token=settings.bot_token) #, session=session)
dp = Dispatcher()


@dp.message(Command("start"))
async def message_start(message: Message):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    user = await get_tg_user(message.from_user)
    if user is None: return

    status = user.expires_at >= datetime.now()
    text = "GymMoodBot\n\n"
    if status:
        expires_delta = (user.expires_at - datetime.now()).total_seconds()
        days = int(expires_delta // (24 * 60 * 60))
        hours = int((expires_delta % (24 * 60 * 60)) // (60 * 60))
        text += f"Подписка закончится через {days} дн., {hours} ч."
    else:
        text += "Подписка неактивна"

    inline_keyboard = []
    if user.tg_id in settings.admin_users:
        inline_keyboard.append([InlineKeyboardButton(text="Админка", callback_data="admin")])
    inline_keyboard.append([InlineKeyboardButton(text="Кастомизация", callback_data="customize")])
    kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer(text, reply_markup=kb)


@dp.callback_query(F.data == "admin")
async def callback_admin(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return
    user = await get_tg_user(callback.from_user)
    if user is None: return

    all_users = await get_users()
    text = "Админ панель\n\n"
    text += "Статистика:\n"
    text += f"Пользователей: {len(all_users)}\n"
    text += f"Активных пользователей: {len([0 for user in all_users if user.expires_at > datetime.now()])}\n"

    inline_keyboard = [
        [InlineKeyboardButton(text="Добавить пользователя", callback_data="add_user"),
         InlineKeyboardButton(text="Продлить пользователя", callback_data="renew_user")],
        [InlineKeyboardButton(text="Забанить пользователя", callback_data="ban_user")]
    ]
    if callback.from_user.id == settings.main_admin:
        inline_keyboard.append([InlineKeyboardButton(text="Добавить администратора", callback_data="add_admin")])
    kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


async def main():
    await create_all()
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


asyncio.run(main())
