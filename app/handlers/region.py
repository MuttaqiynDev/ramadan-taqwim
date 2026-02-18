from aiogram import Router
from aiogram.types import CallbackQuery

from app.keyboards.inline import regions_grid_kb
from app.keyboards.reply import main_menu_kb
from app.services.regions import get_region_by_code
from app.db.repo_users import UsersRepo

router = Router()

@router.callback_query(lambda c: c.data == "region:open")
async def region_open(c: CallbackQuery):
    await c.message.answer("Viloyatni tanlang:", reply_markup=regions_grid_kb())
    await c.answer()

@router.callback_query(lambda c: c.data.startswith("region:set:"))
async def region_set(c: CallbackQuery, users_repo: UsersRepo):
    code = c.data.split(":")[-1]
    await users_repo.set_region_code(c.from_user.id, code)

    reg = get_region_by_code(code)
    title = reg.title if reg else code

    await c.message.answer(
        f"✅ Tanlandi: <b>{title}</b>\n\nEndi menyudan tanlang 👇",
        reply_markup=main_menu_kb(),
    )
    await c.answer("Saqladim ✅")
