from __future__ import annotations
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from datetime import datetime, timedelta, date

from app.keyboards.inline import pick_region_entry_kb
from app.services.regions import get_region_by_code
from app.services.dates import today, tomorrow
from app.services.dua import SUHOOR_DUA, IFTAR_DUA
from app.services.islom_api import IslomApiError
from app.services.formatters import fmt_day
from app.services.calendar_image import DayRow, render_calendar_image
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from app.db.repo_users import UsersRepo
from app.db.repo_cache import CacheRepo
from app.services.islom_api import IslomApiClient
from app.config import Config
from app.services.regions import REGION_MAP

router = Router()





async def ensure_region(m: Message, users_repo: UsersRepo):
    code = await users_repo.get_region_code(m.from_user.id)
    if not code:
        await m.answer("Avval viloyatingizni tanlang 👇", reply_markup=pick_region_entry_kb())
        return None
    reg = get_region_by_code(code)
    if not reg:
        await m.answer("Viloyat topilmadi. Qayta tanlang 👇", reply_markup=pick_region_entry_kb())
        return None
    return reg

async def get_suhoor_iftar(
    cache_repo: CacheRepo,
    islom_client: IslomApiClient,
    region_api: str,
    d: date
):
    date_ymd = d.isoformat()
    cached = await cache_repo.get_daily(region_api, date_ymd)
    if cached:
        return cached[0], cached[1]

    data = await islom_client.daily(region_api, d)
    times = data.get("times") or {}
    suhoor = times.get("tong_saharlik")
    iftar = times.get("shom_iftor")
    if not suhoor or not iftar:
        raise RuntimeError("API javobida kerakli vaqt topilmadi")

    await cache_repo.set_daily(region_api, date_ymd, suhoor, iftar, data)
    return suhoor, iftar

@router.message(lambda m: m.text == "Duo")
async def menu_duo(m: Message, users_repo: UsersRepo):
    reg = await ensure_region(m, users_repo)
    if not reg:
        return
    await m.answer(SUHOOR_DUA, parse_mode="Markdown")
    await m.answer(IFTAR_DUA, parse_mode="Markdown")



@router.message(lambda m: m.text == "Bugungi vaqt")
async def menu_today(m: Message,
    users_repo: UsersRepo,
    cache_repo: CacheRepo,
    islom_client: IslomApiClient,
    cfg: Config):
    reg = await ensure_region(m, users_repo)
    if not reg:
        return
    try:
        d = today(cfg.tz)
        suhoor, iftar = await get_suhoor_iftar(cache_repo, islom_client, reg.api_name, d)
        await m.answer(fmt_day(reg.title, d, suhoor, iftar))
    except IslomApiError as e:
        await m.answer(f"🤷‍♂️ Ma'lumot topilmadi.\n\nTexnik xabarlik: {e}")

@router.message(lambda m: m.text == "Ertaga")
async def menu_tomorrow(
    m: Message,
    users_repo: UsersRepo,
    cache_repo: CacheRepo,
    islom_client: IslomApiClient,
    cfg: Config
):
    reg = await ensure_region(m, users_repo)
    if not reg:
        return
    try:
        d = tomorrow(cfg.tz)
        suhoor, iftar = await get_suhoor_iftar(cache_repo, islom_client, reg.api_name, d)
        await m.answer(fmt_day(reg.title, d, suhoor, iftar))
    except IslomApiError as e:
        await m.answer(f"🤷‍♂️ Ma'lumot topilmadi.\n\nTexnik xabarlik: {e}")





@router.message(lambda m: m.text == "To'liq taqvim")
async def menu_full_calendar(
    m: Message,
    users_repo: UsersRepo,
    cache_repo: CacheRepo,
    islom_client: IslomApiClient,
    cfg: Config
):
    reg = await ensure_region(m, users_repo)
    if not reg:
        return

    start = datetime.fromisoformat(cfg.ramadan_start).date()
    days = cfg.ramadan_days

    # 30 kunlik ro‘yxat (monthly + fallback daily)
    def ym_key(d): return f"{d.year:04d}-{d.month:02d}"

    months = {ym_key(start), ym_key(start + timedelta(days=days-1))}
    month_data: dict[str, list[dict]] = {}

    for ym in months:
        y, mo = ym.split("-")
        y, mo = int(y), int(mo)
        cached = await cache_repo.get_monthly_raw(reg.api_name, ym)
        if cached is None:
            try:
                raw = await islom_client.monthly(reg.api_name, mo)
            except IslomApiError:
                raw = []
            
            await cache_repo.set_monthly_raw(reg.api_name, ym, raw)
            month_data[ym] = raw
        else:
            month_data[ym] = cached
            
    # Check if we have any data
    total_items = sum(len(v) for v in month_data.values())
    if total_items == 0:
        await m.answer(f"⚠️ <b>{reg.title}</b> uchun taqvim ma'lumotlari hozircha topilmadi.\nTez orada qo'shiladi.")
        return

    lookup = {}
    for raw_list in month_data.values():
        for item in raw_list:
            d_str = str(item.get("date", ""))[:10]
            times = item.get("times") or {}
            s = times.get("tong_saharlik")
            f = times.get("shom_iftor")
            if d_str and s and f:
                lookup[d_str] = (s, f)

    rows: list[DayRow] = []
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.isoformat()
        if key in lookup:
            s, f = lookup[key]
        else:
            s, f = await get_suhoor_iftar(cache_repo, islom_client, reg.api_name, d)
        rows.append(DayRow(d=d, suhoor=s, iftar=f))

    # Text representation
    text_lines = ["<pre>Sana       | Saharlik | Iftor"]
    for row in rows:
        text_lines.append(f"{row.d.isoformat()} | {row.suhoor:<8} | {row.iftar}")
    text_lines.append("</pre>")
    
    await m.answer("\n".join(text_lines) + "\n\n@MuttaqiynDevbot")


    img_bytes = render_calendar_image(f"Ramazon taqvimi — {reg.title}", rows)
    photo = BufferedInputFile(img_bytes, filename="ramazon-taqvim.png")

    end_date = rows[-1].d.isoformat() if rows else start.isoformat()

    caption = (
        f"📍 Viloyat: <b>{reg.title}</b>\n"
        f"🗓 To'liq taqvim ({start.isoformat()} dan {end_date} gacha)\n"
        f"\n@MuttaqiynDevbot"
    )

    await m.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )
