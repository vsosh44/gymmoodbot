import re
from datetime import datetime, UTC, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from src.routers.admin import get_admin_panel
from src.types.schemas import User
from src.services import add_user
from src.utils.tg_check import admin_check, get_tg_user

router = Router()


class AddUserState(StatesGroup):
    tg_id = State()
    mood_id = State()
    classname = State()


@router.callback_query(F.data == "add_user")
async def callback_add_user(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return
    if not admin_check(callback.from_user): return
    user = await get_tg_user(callback.from_user)
    if user is None: return

    await callback.message.answer("Введите число - telegram id пользователя")
    await state.set_state(AddUserState.tg_id)


@router.message(AddUserState.tg_id)
async def process_username(message: Message, state: FSMContext):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    if not admin_check(message.from_user): return

    if message.text is None:
        await message.answer("Неверный формат данных")
        return

    text = message.text
    if not text.isdigit():
        await message.answer("Введите число - telegram id пользователя")
        return
    await state.update_data(tg_id=int(text))

    await message.answer("Введите число - номер пользователя в системе")
    await state.set_state(AddUserState.mood_id)


@router.message(AddUserState.mood_id)
async def process_mood_id(message: Message, state: FSMContext):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    if not admin_check(message.from_user): return

    if message.text is None:
        await message.answer("Неверный формат данных")
        return

    if not message.text.isdigit():
        await message.answer("Введите число - номер пользователя в системе")
        return
    await state.update_data(mood_id=int(message.text))

    await message.answer("Введите класс пользователя")
    await state.set_state(AddUserState.classname)


@router.message(AddUserState.classname)
async def process_classname(message: Message, state: FSMContext):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    if not admin_check(message.from_user): return

    if message.text is None:
        await message.answer("Неверный формат данных")
        return

    classname = message.text.strip()
    if re.fullmatch(r"(?:[1-9]|1[01])[А-ЯЁ].*", classname) is None:
        await message.answer("Введите правильное название класса. Например: 10Б")
        return
    await state.update_data(classname=classname)

    data = await state.get_data()

    tg_id = data.get("tg_id", 0)
    mood_id = data.get("mood_id", 0)
    classname = data.get("classname", "")

    expires_at = datetime.now(UTC) + timedelta(days=30)
    user = User(
        tg_id=tg_id,
        mood_id=mood_id,
        classname=classname,
        expires_at=expires_at,
        next_mood_at=datetime.now(UTC)
    )
    await add_user(user)

    await message.answer("Пользователь успешно добавлен")
    await state.clear()

    text, kb = await get_admin_panel()
    await message.answer(text, reply_markup=kb)
