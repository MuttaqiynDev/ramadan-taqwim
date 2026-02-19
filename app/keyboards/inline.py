from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.services.regions import REGIONS


def pick_region_entry_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📍 Viloyatni tanlash", callback_data="region:open")
    return b.as_markup()


def regions_grid_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for r in REGIONS:
        b.button(text=r.title, callback_data=f"region:set:{r.code}")
    b.adjust(2)
    return b.as_markup()


def webapp_open_kb(webapp_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📱 Ochish", web_app=WebAppInfo(url=webapp_url))
    return b.as_markup()
