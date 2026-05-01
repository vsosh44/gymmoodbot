import re
from datetime import datetime, UTC, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InaccessibleMessage, Message, InlineKeyboardButton, InlineKeyboardMarkup

from src.routers.admin import get_admin_panel
from src.types.enums import MoodType
from src.types.schemas import User
from src.services import add_user
from src.utils.tg_check import admin_check, get_tg_user

router = Router()


def get_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_add_user")]
        ]
    )


class AddUserState(StatesGroup):
    tg_id = State()
    mood_id = State()
    classname = State()


@router.callback_query(F.data == "cancel_add_user")
async def callback_cancel_add_user(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return
    if not admin_check(callback.from_user): return

    await state.clear()

    text, kb = await get_admin_panel()
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "add_user")
async def callback_add_user(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return
    if not admin_check(callback.from_user): return
    user = await get_tg_user(callback.from_user)
    if user is None: return

    await callback.message.answer(
        "Введите число - telegram id пользователя",
        reply_markup=get_cancel_kb(),
    )
    await state.set_state(AddUserState.tg_id)
    await callback.answer()


@router.message(AddUserState.tg_id)
async def process_username(message: Message, state: FSMContext):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    if not admin_check(message.from_user): return

    if message.text is None:
        await message.answer(
            "Неверный формат данных",
            reply_markup=get_cancel_kb(),
        )
        return

    text = message.text
    if not text.isdigit():
        await message.answer(
            "Введите число - telegram id пользователя",
            reply_markup=get_cancel_kb(),
        )
        return
    await state.update_data(tg_id=int(text))

    await message.answer(
        "Введите число - номер пользователя в системе",
        reply_markup=get_cancel_kb(),
    )
    await state.set_state(AddUserState.mood_id)


@router.message(AddUserState.mood_id)
async def process_mood_id(message: Message, state: FSMContext):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    if not admin_check(message.from_user): return

    if message.text is None:
        await message.answer(
            "Неверный формат данных",
            reply_markup=get_cancel_kb(),
        )
        return

    if not message.text.isdigit():
        await message.answer(
            "Введите число - номер пользователя в системе",
            reply_markup=get_cancel_kb(),
        )
        return
    await state.update_data(mood_id=int(message.text))

    await message.answer(
        "Введите класс пользователя",
        reply_markup=get_cancel_kb(),
    )
    await state.set_state(AddUserState.classname)


@router.message(AddUserState.classname)
async def process_classname(message: Message, state: FSMContext):
    if message is None or isinstance(message, InaccessibleMessage) or message.from_user is None: return
    if not admin_check(message.from_user): return

    if message.text is None:
        await message.answer(
            "Неверный формат данных",
            reply_markup=get_cancel_kb(),
        )
        return

    classname = message.text.strip()
    if re.fullmatch(r"(?:[1-9]|1[01])[А-ЯЁ].*", classname) is None:
        await message.answer(
            "Введите правильное название класса. Например: 10Б",
            reply_markup=get_cancel_kb(),
        )
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
        mood_type=MoodType.random,
        next_mood_at=datetime.now(UTC),
        set_mood_on_weekends=False,
    )
    try:
        await add_user(user)
    except Exception as e:
        await message.answer(f"Ошибка при добавлении: {e}")
    else:
        await message.answer("Пользователь успешно добавлен")
    finally:
        await state.clear()
        text, kb = await get_admin_panel()
        await message.answer(text, reply_markup=kb)
