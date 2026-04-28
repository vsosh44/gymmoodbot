from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, InlineKeyboardButton, InlineKeyboardMarkup

from src.services import update_user_mood_type
from src.types.enums import MoodType
from src.utils.tg_check import get_tg_user

router = Router()


def get_mood_title(mood_type: MoodType) -> str:
    titles = {
        MoodType.sunny: "Солнечное",
        MoodType.creative: "Творческое",
        MoodType.alarming: "Тревожное",
        MoodType.tired: "Усталое",
        MoodType.peaceful: "Спокойное",
        MoodType.random: "Случайное",
    }

    return titles.get(mood_type, mood_type.name)


def get_mood_description(mood_type: MoodType) -> str:
    if mood_type == MoodType.random:
        return "Случайное настроение: солнечное, творческое или спокойное"

    return get_mood_title(mood_type)


def get_customize_menu_text(user) -> str:
    mood_type = user.mood_type

    return (
        "✏️ <u><strong>Кастомизация</strong></u>\n\n"
        "Здесь можно настроить поведение бота под себя.\n\n"
        "⚙️ <strong>Текущие настройки</strong>\n"
        f"• Тип настроения: <code>{get_mood_title(mood_type)}</code>\n"
        f"• Значение: <code>{get_mood_description(mood_type)}</code>"
    )


def get_customize_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Тип настроения", callback_data="customize_mood_type")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_start")],
        ]
    )


def get_mood_type_menu_text(user) -> str:
    mood_type = user.mood_type

    return (
        "🎭 <u><strong>Тип настроения</strong></u>\n\n"
        f"Текущее настроение: <code>{get_mood_title(mood_type)}</code>\n"
        f"Значение: <code>{get_mood_description(mood_type)}</code>\n\n"
        "Выберите новый тип настроения:"
    )


def get_mood_type_menu_kb() -> InlineKeyboardMarkup:
    buttons = []

    for mood_type in MoodType:
        buttons.append(
            InlineKeyboardButton(
                text=get_mood_title(mood_type),
                callback_data=f"set_mood_type:{mood_type.name}",
            )
        )
    inline_keyboard = [[*buttons[0:3]], [*buttons[3:6]], [InlineKeyboardButton(text="Назад", callback_data="customize")]]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


@router.callback_query(F.data == "customize")
async def callback_customize(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return

    user = await get_tg_user(callback.from_user)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        get_customize_menu_text(user),
        reply_markup=get_customize_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "customize_mood_type")
async def callback_customize_mood_type(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return

    user = await get_tg_user(callback.from_user)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        get_mood_type_menu_text(user),
        reply_markup=get_mood_type_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_mood_type:"))
async def callback_set_mood_type(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage): return

    mood_type_name = callback.data.removeprefix("set_mood_type:") if callback.data is not None else ""

    try:
        mood_type = MoodType[mood_type_name]
    except KeyError:
        await callback.answer("Неизвестный тип настроения", show_alert=True)
        return

    updated = await update_user_mood_type(callback.from_user.id, mood_type)
    if not updated:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    user = await get_tg_user(callback.from_user)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        get_customize_menu_text(user),
        reply_markup=get_customize_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
