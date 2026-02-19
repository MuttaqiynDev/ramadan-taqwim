"""Shared data-fetching logic used by both bot handlers and FastAPI endpoints."""
from __future__ import annotations
import logging
from datetime import date, timedelta, datetime

from app.db.repo_cache import CacheRepo
from app.services.islom_api import IslomApiClient, IslomApiError
from app.services.calendar_image import DayRow
from app.services.andijan_times import ANDIJAN_TIMES

logger = logging.getLogger(__name__)

# Regions that use static fallback data instead of API
STATIC_REGIONS = {"Andijan"}


async def get_suhoor_iftar(
    cache_repo: CacheRepo,
    islom_client: IslomApiClient,
    region_api: str,
    d: date,
) -> tuple[str, str]:
    date_ymd = d.isoformat()

    # Check static fallback first (e.g. Andijan)
    if region_api in STATIC_REGIONS and date_ymd in ANDIJAN_TIMES:
        return ANDIJAN_TIMES[date_ymd]

    # Check daily cache
    cached = await cache_repo.get_daily(region_api, date_ymd)
    if cached:
        return cached[0], cached[1]

    # For static regions without data for this date, don't call API
    if region_api in STATIC_REGIONS:
        raise RuntimeError(f"{region_api} uchun {date_ymd} sanasida ma'lumot topilmadi")

    # Try daily API
    data = await islom_client.daily(region_api, d)
    times = data.get("times") or {}
    suhoor = times.get("tong_saharlik")
    iftar = times.get("shom_iftor")
    if not suhoor or not iftar:
        raise RuntimeError("API javobida kerakli vaqt topilmadi")

    await cache_repo.set_daily(region_api, date_ymd, suhoor, iftar, data)
    return suhoor, iftar


async def get_monthly_rows(
    cache_repo: CacheRepo,
    islom_client: IslomApiClient,
    region_api: str,
    ramadan_start: str,
    ramadan_days: int,
) -> list[DayRow]:
    start = datetime.fromisoformat(ramadan_start).date()
    days = ramadan_days

    # For static regions, build rows directly from hardcoded data
    if region_api in STATIC_REGIONS:
        rows: list[DayRow] = []
        for i in range(days):
            d = start + timedelta(days=i)
            key = d.isoformat()
            if key in ANDIJAN_TIMES:
                s, f = ANDIJAN_TIMES[key]
            else:
                s, f = "—", "—"
            rows.append(DayRow(d=d, suhoor=s, iftar=f))
        return rows

    # --- API-based regions ---

    def ym_key(d):
        return f"{d.year:04d}-{d.month:02d}"

    months = {ym_key(start), ym_key(start + timedelta(days=days - 1))}
    lookup: dict[str, tuple[str, str]] = {}

    # Step 1: Try monthly endpoint (cached or fresh)
    for ym in months:
        y, mo = ym.split("-")
        y, mo = int(y), int(mo)

        cached = await cache_repo.get_monthly_raw(region_api, ym)
        if cached is not None and len(cached) > 0:
            # Use valid cached monthly data
            raw_list = cached
        else:
            # Try fresh monthly API
            try:
                raw_list = await islom_client.monthly(region_api, mo)
            except IslomApiError as e:
                logger.warning(f"Monthly API failed for {region_api}/{ym}: {e}")
                raw_list = []

            # Only cache non-empty results
            if raw_list:
                await cache_repo.set_monthly_raw(region_api, ym, raw_list)

        # Extract times from monthly data
        for item in raw_list:
            d_str = str(item.get("date", ""))[:10]
            times = item.get("times") or {}
            s = times.get("tong_saharlik")
            f = times.get("shom_iftor")
            if d_str and s and f:
                lookup[d_str] = (s, f)

    # Step 2: Build rows, falling back to daily API for missing dates
    rows: list[DayRow] = []
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.isoformat()

        if key in lookup:
            s, f = lookup[key]
        else:
            # Try daily API as fallback
            try:
                s, f = await get_suhoor_iftar(cache_repo, islom_client, region_api, d)
            except Exception as e:
                logger.warning(f"Daily fallback failed for {region_api}/{key}: {e}")
                s, f = "—", "—"

        rows.append(DayRow(d=d, suhoor=s, iftar=f))

    return rows
