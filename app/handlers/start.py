from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from app.keyboards.inline import pick_region_entry_kb, webapp_open_kb
from app.services.regions import get_region_by_code
from app.db.repo_users import UsersRepo
from app.config import Config

router = Router()


@router.message(CommandStart())
async def start(m: Message, users_repo: UsersRepo, cfg: Config):
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
        f"Assalomu alaykum!\n✅ Tanlangan viloyat: <b>{title}</b>\n\n"
        "Ramazon taqvimini ochish uchun pastdagi tugmani bosing 👇",
        reply_markup=webapp_open_kb(cfg.webapp_url),
    )
    # Remove any leftover reply keyboard
    await m.answer("⌨️", reply_markup=ReplyKeyboardRemove())
    # Delete the cleanup message immediately
    try:
        await m.bot.delete_message(m.chat.id, m.message_id + 2)
    except Exception:
        pass
