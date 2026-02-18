from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

@dataclass(frozen=True)
class DayRow:
    d: date
    suhoor: str
    iftar: str

def render_calendar_image(title: str, rows: list[DayRow]) -> bytes:
    W = 900
    row_h = 36
    pad = 24
    header_h = 70
    table_h = (len(rows) + 1) * row_h
    H = pad * 2 + header_h + table_h

    img = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans.ttf", 26)
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
        font_b = ImageFont.truetype("DejaVuSans.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font = ImageFont.load_default()
        font_b = ImageFont.load_default()

    # Title
    dr.text((pad, pad), title, fill="black", font=font_title)

    y0 = pad + header_h
    x_date, x_suhoor, x_iftar = pad, 420, 650

    # Header row
    dr.rectangle((pad, y0, W - pad, y0 + row_h), outline="black", width=1)
    dr.text((x_date, y0 + 8), "Sana", fill="black", font=font_b)
    dr.text((x_suhoor, y0 + 8), "Saharlik", fill="black", font=font_b)
    dr.text((x_iftar, y0 + 8), "Iftorlik", fill="black", font=font_b)

    # Rows
    for i, r in enumerate(rows, start=1):
        y = y0 + i * row_h
        dr.rectangle((pad, y, W - pad, y + row_h), outline="black", width=1)
        dr.text((x_date, y + 8), r.d.isoformat(), fill="black", font=font)
        dr.text((x_suhoor, y + 8), r.suhoor, fill="black", font=font)
        dr.text((x_iftar, y + 8), r.iftar, fill="black", font=font)

    bio = BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()
