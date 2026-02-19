"""Menu handler — all reply-keyboard text handlers removed.
Kept as router placeholder for future inline-based commands."""
from __future__ import annotations
from aiogram import Router

router = Router()

# All reply-keyboard text handlers (Duo, Bugungi vaqt, Ertaga, To'liq taqvim)
# have been removed. Their functionality is now in the WebApp via FastAPI endpoints.
# Shared data logic lives in app/services/data_service.py
