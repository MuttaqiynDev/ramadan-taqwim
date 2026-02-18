from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.inline import pick_region_entry_kb
from app.keyboards.reply import main_menu_kb
from app.services.regions import get_region_by_code
from app.db.repo_users import UsersRepo

router = Router()

@router.message(CommandStart())
async def start(m: Message, users_repo: UsersRepo):
    code = await users_repo.get_region_code(m.from_user.id)

    if not code:
        await m.answer(
            "Assalomu alaykum! Ramazon taqvimi botiga xush kelibsiz.\n\n"
            "Davom etish uchun viloyatingizni tanlang 👇",
            reply_markup=pick_region_entry_kb(),
        )
        return

    reg = get_region_by_code(code)
    title = reg.title if reg else code
    await m.answer(
        f"Assalomu alaykum!\n✅ Tanlangan viloyat: <b>{title}</b>\n\nMenyudan foydalaning 👇",
        reply_markup=main_menu_kb(),
    )
