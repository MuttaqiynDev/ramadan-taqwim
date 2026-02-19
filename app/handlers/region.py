from aiogram import Router
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from app.keyboards.inline import regions_grid_kb, webapp_open_kb
from app.services.regions import get_region_by_code
from app.db.repo_users import UsersRepo
from app.config import Config

router = Router()


@router.callback_query(lambda c: c.data == "region:open")
async def region_open(c: CallbackQuery):
    await c.message.answer("Viloyatni tanlang:", reply_markup=regions_grid_kb())
    await c.answer()


@router.callback_query(lambda c: c.data.startswith("region:set:"))
async def region_set(c: CallbackQuery, users_repo: UsersRepo, cfg: Config):
    code = c.data.split(":")[-1]
    await users_repo.set_region_code(c.from_user.id, code)

    reg = get_region_by_code(code)
    title = reg.title if reg else code

    # Remove any leftover reply keyboard
    await c.message.answer("⌨️", reply_markup=ReplyKeyboardRemove())
    try:
        await c.bot.delete_message(c.message.chat.id, c.message.message_id + 1)
    except Exception:
        pass

    await c.message.answer(
        f"✅ Tanlandi: <b>{title}</b>\n\nTaqvimni ochish uchun pastdagi tugmani bosing 👇",
        reply_markup=webapp_open_kb(cfg.webapp_url),
    )
    await c.answer("Saqladim ✅")
