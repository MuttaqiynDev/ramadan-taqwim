from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import aiohttp

@dataclass(frozen=True)
class IslomApiConfig:
    base_url: str = "https://islomapi.uz"

# app/services/islom_api.py

class IslomApiError(RuntimeError):
    pass

async def _read_json_or_text(resp):
    ct = (resp.headers.get("Content-Type") or "").lower()
    text = await resp.text()

    # JSON bo‘lsa parse qilib ko‘ramiz
    if "application/json" in ct:
        try:
            import json
            return json.loads(text), text
        except Exception:
            return None, text

    return None, text



class IslomApiClient:
    def __init__(self, session: aiohttp.ClientSession, cfg: IslomApiConfig = IslomApiConfig()):
        self.session = session
        self.cfg = cfg

    async def _get_json(self, url: str, params: dict) -> object:
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise IslomApiError(f"HTTP {resp.status}: {text[:120]}")
                # Ba’zan content-type noto‘g‘ri bo‘ladi; shuning uchun content_type=None
                return await resp.json(content_type=None)
        except aiohttp.ClientError as e:
            raise IslomApiError(f"Network error: {e}") from e
        except aiohttp.ContentTypeError as e:
            raise IslomApiError(f"Invalid JSON (content-type): {e}") from e

    async def daily(self, region_api: str, d: date) -> dict:
        url = f"{self.cfg.base_url}/api/daily"
        params = {"region": region_api, "month": str(d.month), "day": str(d.day)}
        data = await self._get_json(url, params)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        elif isinstance(data, list) and not data:
            raise IslomApiError("Ma'lumot topilmadi (API bo'sh javob qaytardi)")

        if data is None:
             raise IslomApiError("Ma'lumot topilmadi (API null qaytardi)")

        if not isinstance(data, dict):
            raise IslomApiError(f"daily: expected JSON object, got {type(data).__name__}: {str(data)[:200]}")
        return data

    async def monthly_raw(self, region_api: str, month: int) -> list[dict]:
        """
        islomapi oy parametri ba'zan 0-based bo'ladi.
        Shuning uchun bo'sh list qaytsa month-1 bilan qayta urinib ko'ramiz.
        """
        url = f"{self.cfg.base_url}/api/monthly"

        async def fetch(m: int) -> list[dict]:
            data = await self._get_json(url, {"region": region_api, "month": str(m)})
            if not isinstance(data, list):
                raise IslomApiError(f"monthly: expected JSON array, got {type(data).__name__}")
            # dict bo'lmaganlarni olib tashlaymiz
            return [x for x in data if isinstance(x, dict)]

        out = await fetch(month)

        # ✅ Asosiy fix: agar bo'sh bo'lsa 0-based variantni sinash
        if not out and month > 0:
            out = await fetch(month - 1)

        if not out:
            raise IslomApiError(f"monthly: empty list. region={region_api!r} month={month!r} (also tried {month-1 if month>0 else None})")

        return out


    async def monthly(self, region_api: str, month: int) -> list[dict]:
        return await self.monthly_raw(region_api, month)



    async def get_day_times_from_monthly(self, region_api: str, d: date) -> tuple[str, str]:
        raw_list = await self.monthly_raw(region_api, d.month)
        target = d.isoformat()  # YYYY-MM-DD

        # 1) avval date match qilamiz (date yoki day)
        candidates: list[dict] = []

        for item in raw_list:
            # ba'zida "date" bo‘ladi, ba'zida "day" bo‘ladi
            d_str = str(item.get("date", ""))[:10]
            if d_str == target:
                candidates.append(item)
                continue

            day = item.get("day")
            if isinstance(day, int) and day == d.day:
                candidates.append(item)
                continue
            if isinstance(day, str) and day.isdigit() and int(day) == d.day:
                candidates.append(item)
                continue

        if not candidates:
            # hech bo'lmasa 1 ta itemdan times olishga urinib ko‘ramiz
            candidates = raw_list

        # 2) times formatlari: times dict bo'lishi mumkin yoki to'g'ridan-to'g'ri item ichida bo'lishi mumkin
        def pick_times(item: dict) -> tuple[str | None, str | None]:
            times = item.get("times")
            if isinstance(times, dict):
                suhoor = times.get("tong_saharlik") or times.get("saharlik") or times.get("suhoor")
                iftar = times.get("shom_iftor") or times.get("iftor") or times.get("iftar")
                return suhoor, iftar

            # fallback: root ichidan qidirish
            suhoor = item.get("tong_saharlik") or item.get("saharlik") or item.get("suhoor")
            iftar = item.get("shom_iftor") or item.get("iftor") or item.get("iftar")
            return suhoor, iftar

        for it in candidates:
            suhoor, iftar = pick_times(it)
            if suhoor and iftar:
                return str(suhoor), str(iftar)

        raise IslomApiError("monthly: could not extract times (check region_api name)")
