import asyncio
import os
import logging
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)

# ========================= НАСТРОЙКИ =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not BOT_TOKEN or not WEBAPP_URL:
    raise ValueError("❌ BOT_TOKEN и WEBAPP_URL обязательны! Добавь их в Render → Environment Variables")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================= МОДЕЛИ =========================
class UserProfile(BaseModel):
    id: int
    name: str
    skills: List[str]
    city: str
    price: int
    is_premium: bool = False
    rating: float = 4.8


# ========================= ДАННЫЕ =========================
users_db: List[UserProfile] = [
    UserProfile(id=1, name="Иван Петров", skills=["Python", "FastAPI", "PostgreSQL"], city="Москва", price=2500, is_premium=True, rating=4.9),
    UserProfile(id=2, name="Анна Смирнова", skills=["Figma", "UI/UX", "Framer"], city="Удалённо", price=1800, is_premium=False, rating=5.0),
    UserProfile(id=3, name="Дмитрий Соколов", skills=["React Native", "TypeScript", "Flutter"], city="Санкт-Петербург", price=3200, is_premium=True, rating=4.7),
]

# ========================= ИНИЦИАЛИЗАЦИЯ =========================
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
app = FastAPI(title="Биржа Специалистов")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================= БОТ =========================
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Открыть Биржу", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="⭐ Купить Boost (50 ⭐️)", callback_data="buy_boost")]
    ])
    await message.answer(
        "👋 <b>Добро пожаловать на Биржу Специалистов!</b>\n\n"
        "Найди исполнителя или продвинь свою анкету.",
        reply_markup=kb
    )


@dp.callback_query(F.data == "buy_boost")
async def buy_boost_handler(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Premium Boost",
        description="Подъём анкеты в ТОП на 7 дней",
        payload="premium_boost_7d",
        currency="XTR",
        prices=[LabeledPrice(label="Premium Boost", amount=50)],
        provider_token="",
    )


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    await message.answer("🎉 <b>Оплата прошла успешно!</b>\nВаш профиль теперь в ТОПе на 7 дней!")


# ========================= API =========================
@app.get("/api/search")
async def search_candidates(
    skill: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):
    results = users_db.copy()

    if skill:
        skill_lower = skill.lower()
        results = [u for u in results if any(skill_lower in s.lower() for s in u.skills)]
    if city:
        city_lower = city.lower()
        results = [u for u in results if city_lower in u.city.lower()]

    results.sort(key=lambda x: (x.is_premium, x.price), reverse=True)
    return results


@app.get("/")
async def root():
    return {"status": "ok", "message": "Биржа работает"}


# ========================= ЗАПУСК =========================
async def main():
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Биржа запущена на порту {port}")

    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
await asyncio.gather(
        server.serve(),
        dp.start_polling(bot),
        return_exceptions=True
    )


if name == "__main__":
    asyncio.run(main())
