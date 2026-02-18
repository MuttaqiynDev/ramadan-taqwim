from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="Duo"))
    b.row(KeyboardButton(text="Bugungi vaqt"), KeyboardButton(text="Ertaga"))
    b.row(KeyboardButton(text="To'liq taqvim"))
    return b.as_markup(resize_keyboard=True)
