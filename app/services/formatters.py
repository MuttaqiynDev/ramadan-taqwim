from datetime import date

def fmt_day(region_title: str, d: date, suhoor: str, iftar: str) -> str:
    return (
        f"📍 Viloyat: <b>{region_title}</b>\n"
        f"📅 Sana: {d.isoformat()}\n\n"
        f"🌙 Saharlik: {suhoor}\n"
        f"🌅 Iftorlik: {iftar}\n\n"
        f"@MuttaqiynDevbot\n\n"
        f"<i>Eslatma: Vaqtlar islom.uz saytidan olingan va Shaxringizga qarab farq qilishi mumkin. Boshqa manbalardan ham tekshirib ko‘ring.</i>"
    )
