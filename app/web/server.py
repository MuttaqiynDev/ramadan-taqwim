"""FastAPI web server — serves WebApp and API endpoints."""
from __future__ import annotations
import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.web.auth import extract_user_id
from app.services.regions import get_region_by_code, REGIONS
from app.services.dates import today as get_today
from app.services.dua import SUHOOR_DUA, IFTAR_DUA
from app.services.data_service import get_suhoor_iftar, get_monthly_rows
from app.services.calendar_image import render_calendar_image

STATIC_DIR = Path(__file__).parent / "static"

# Hijri month names
HIJRI_MONTHS = [
    "", "Muharram", "Safar", "Rabi ul-Avval", "Rabi us-Soniy",
    "Jumadal-Ula", "Jumadal-Uxro", "Rajab", "Sha'bon",
    "Ramazon", "Shavvol", "Zulqa'da", "Zulhijja"
]

UZ_WEEKDAYS = {
    0: "Dushanba", 1: "Seshanba", 2: "Chorshanba", 3: "Payshanba",
    4: "Juma", 5: "Shanba", 6: "Yakshanba"
}

UZ_MONTHS_SHORT = {
    1: "Yan", 2: "Fev", 3: "Mar", 4: "Apr", 5: "May", 6: "Iyn",
    7: "Iyl", 8: "Avg", 9: "Sen", 10: "Okt", 11: "Noy", 12: "Dek"
}


def create_app() -> FastAPI:
    app = FastAPI(title="Ramazon Taqvimi WebApp")

    # Mount static files (CSS, JS)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/webapp", response_class=HTMLResponse)
    async def serve_webapp():
        index_path = STATIC_DIR / "index.html"
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    @app.get("/api/today")
    async def api_today(request: Request, initData: str = Query(...)):
        bot_token = request.app.state.cfg.bot_token
        try:
            user_id = extract_user_id(initData, bot_token)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

        users_repo = request.app.state.users_repo
        cache_repo = request.app.state.cache_repo
        islom_client = request.app.state.islom_client
        cfg = request.app.state.cfg

        user = await users_repo.get_user(user_id)
        if not user or not user["region_code"]:
            raise HTTPException(status_code=400, detail="Region not set")

        reg = get_region_by_code(user["region_code"])
        if not reg:
            raise HTTPException(status_code=400, detail="Invalid region")

        tz = cfg.tz
        d = get_today(tz)

        try:
            suhoor, iftar = await get_suhoor_iftar(cache_repo, islom_client, reg.api_name, d)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"API error: {e}")

        # Calculate next event
        now = datetime.now()
        try:
            from app.services.dates import _get_tz
            import pytz
        except ImportError:
            pass

        from app.services.dates import _get_tz
        tz_obj = _get_tz(tz)
        now = datetime.now(tz_obj)

        suhoor_time = datetime.strptime(suhoor, "%H:%M").replace(
            year=d.year, month=d.month, day=d.day, tzinfo=tz_obj
        )
        iftar_time = datetime.strptime(iftar, "%H:%M").replace(
            year=d.year, month=d.month, day=d.day, tzinfo=tz_obj
        )

        if now < suhoor_time:
            next_event_name = "Saharlik"
            next_event_time = suhoor
            remaining = (suhoor_time - now).total_seconds()
            # Total: from previous iftar to this suhoor
            total = (suhoor_time - iftar_time.replace(day=d.day - 1 if d.day > 1 else d.day)).total_seconds()
            total = ((24 * 60 - iftar_time.hour * 60 - iftar_time.minute) + suhoor_time.hour * 60 + suhoor_time.minute) * 60
        elif now < iftar_time:
            next_event_name = "Iftor"
            next_event_time = iftar
            remaining = (iftar_time - now).total_seconds()
            # Total: from suhoor to iftar
            total = (iftar_time - suhoor_time).total_seconds()
        else:
            # After iftar — show tomorrow's saharlik
            next_event_name = "Saharlik"
            tomorrow = d + timedelta(days=1)
            try:
                s_tom, _ = await get_suhoor_iftar(cache_repo, islom_client, reg.api_name, tomorrow)
                next_event_time = s_tom
                suhoor_tom = datetime.strptime(s_tom, "%H:%M").replace(
                    year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, tzinfo=tz_obj
                )
                remaining = (suhoor_tom - now).total_seconds()
                total = (suhoor_tom - iftar_time).total_seconds()
            except Exception:
                next_event_time = suhoor
                remaining = 0
                total = 1

        # Hijri date approximation (Ramadan 2026 starts ~Feb 18)
        ramadan_start = datetime.fromisoformat(cfg.ramadan_start).date()
        hijri_day = (d - ramadan_start).days + 1
        if 1 <= hijri_day <= 30:
            hijri_str = f"{hijri_day} Ramazon, 1447"
        else:
            hijri_str = ""

        weekday = UZ_WEEKDAYS.get(d.weekday(), "")
        month_short = UZ_MONTHS_SHORT.get(d.month, "")
        greg_str = f"{weekday}, {d.day} {month_short}"

        # Clean duas for WebApp (strip markdown and bot tag)
        def clean_dua(raw: str) -> dict:
            lines = raw.strip().split("\n")
            parts = {"arabic": "", "reading": "", "translation": ""}
            for line in lines:
                line = line.strip().replace("*", "")
                if not line or line.startswith("🌙") or line.startswith("@"):
                    continue
                # Arabic detection: contains Arabic Unicode range
                if any("\u0600" <= ch <= "\u06FF" for ch in line):
                    parts["arabic"] = line
                elif line.startswith("O'qilishi:"):
                    parts["reading"] = line
                elif line.startswith("Ma'nosi:"):
                    parts["translation"] = line
            return parts

        return JSONResponse({
            "gregorian_date": greg_str,
            "hijri_date": hijri_str,
            "region_name": reg.title + " viloyati",
            "suhoor": suhoor,
            "iftar": iftar,
            "next_event_name": next_event_name,
            "next_event_time": next_event_time,
            "remaining_seconds": max(0, int(remaining)),
            "total_seconds": max(1, int(total)),
            "reminder_enabled": user["reminder_enabled"],
            "reminder_offset": user["reminder_offset"],
            "duas": {
                "saharlik": clean_dua(SUHOOR_DUA),
                "iftorlik": clean_dua(IFTAR_DUA),
            },
        })

    @app.get("/api/month")
    async def api_month(request: Request, initData: str = Query(...)):
        bot_token = request.app.state.cfg.bot_token
        try:
            user_id = extract_user_id(initData, bot_token)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

        users_repo = request.app.state.users_repo
        cache_repo = request.app.state.cache_repo
        islom_client = request.app.state.islom_client
        cfg = request.app.state.cfg

        user = await users_repo.get_user(user_id)
        if not user or not user["region_code"]:
            raise HTTPException(status_code=400, detail="Region not set")

        reg = get_region_by_code(user["region_code"])
        if not reg:
            raise HTTPException(status_code=400, detail="Invalid region")

        try:
            rows = await get_monthly_rows(
                cache_repo, islom_client, reg.api_name,
                cfg.ramadan_start, cfg.ramadan_days,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"/api/month error for {reg.api_name}: {e}", exc_info=True)
            rows = []

        calendar_rows = []
        ramadan_start = datetime.fromisoformat(cfg.ramadan_start).date()
        for i, row in enumerate(rows):
            hijri_day = i + 1
            weekday = UZ_WEEKDAYS.get(row.d.weekday(), "")
            calendar_rows.append({
                "day": hijri_day,
                "date": row.d.isoformat(),
                "weekday": weekday,
                "suhoor": row.suhoor,
                "iftar": row.iftar,
            })

        return JSONResponse({
            "region_name": reg.title,
            "calendar_image_url": f"/api/calendar-image?initData={initData}",
            "rows": calendar_rows,
        })

    @app.get("/api/calendar-image")
    async def api_calendar_image(request: Request, initData: str = Query(...)):
        bot_token = request.app.state.cfg.bot_token
        try:
            user_id = extract_user_id(initData, bot_token)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

        users_repo = request.app.state.users_repo
        cache_repo = request.app.state.cache_repo
        islom_client = request.app.state.islom_client
        cfg = request.app.state.cfg

        user = await users_repo.get_user(user_id)
        if not user or not user["region_code"]:
            raise HTTPException(status_code=400, detail="Region not set")

        reg = get_region_by_code(user["region_code"])
        if not reg:
            raise HTTPException(status_code=400, detail="Invalid region")

        try:
            rows = await get_monthly_rows(
                cache_repo, islom_client, reg.api_name,
                cfg.ramadan_start, cfg.ramadan_days,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

        img_bytes = render_calendar_image(f"Ramazon taqvimi — {reg.title}", rows)
        return Response(content=img_bytes, media_type="image/png")

    class SettingsUpdate(BaseModel):
        initData: str
        reminder_enabled: bool | None = None
        reminder_offset: int | None = None
        region_code: str | None = None

    @app.post("/api/settings")
    async def api_settings(request: Request, body: SettingsUpdate):
        bot_token = request.app.state.cfg.bot_token
        try:
            user_id = extract_user_id(body.initData, bot_token)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

        users_repo = request.app.state.users_repo

        if body.region_code is not None:
            reg = get_region_by_code(body.region_code)
            if not reg:
                raise HTTPException(status_code=400, detail="Invalid region")
            await users_repo.set_region_code(user_id, body.region_code)

        if body.reminder_enabled is not None:
            offset = body.reminder_offset or 10
            await users_repo.set_reminder(user_id, body.reminder_enabled, offset)

            # Reschedule reminders for this user
            scheduler = getattr(request.app.state, "scheduler", None)
            if scheduler:
                from app.services.reminders import reschedule_user
                await reschedule_user(
                    scheduler, request.app.state.bot, users_repo,
                    request.app.state.cache_repo, request.app.state.islom_client,
                    request.app.state.cfg, user_id,
                )

        user = await users_repo.get_user(user_id)
        return JSONResponse({"ok": True, "user": user})

    return app
