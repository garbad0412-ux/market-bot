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
    WebAppInfo, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    LabeledPrice, 
    PreCheckoutQuery
)

# ========================= НАСТРОЙКИ =========================

BOT_TOKEN = os.getenv("8629362225:AAFHLuL06lYbVttdcQ0dfmnhuFx576YOvUE")          # Рекомендуется через .env
WEBAPP_URL = os.getenv("https://garbad0412-ux.github.io/market-bot/")

if not BOT_TOKEN or not WEBAPP_URL:
    raise ValueError("BOT_TOKEN и WEBAPP_URL должны быть заданы в переменных окружения!")

# Логирование
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


# ========================= ДАННЫЕ =========================

users_db: List[UserProfile] = [
    UserProfile(
        id=1, 
        name="Иван (Разработчик)", 
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        city="Москва", 
        price=2000, 
        is_premium=True
    ),
    UserProfile(
        id=2, 
        name="Анна (Дизайнер)", 
        skills=["Figma", "UI/UX", "Framer", "Webflow"],
        city="Удалённо", 
        price=1500, 
        is_premium=False
    ),
    UserProfile(
        id=3, 
        name="Дмитрий (Мобилки)", 
        skills=["React Native", "TypeScript", "Flutter", "Kotlin"],
        city="Санкт-Петербург", 
        price=3000, 
        is_premium=False
    ),
]

# ========================= ИНИЦИАЛИЗАЦИЯ =========================

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
app = FastAPI(title="Биржа Труда — Mini App")

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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Открыть Биржу", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="⭐ Купить Boost (50 ⭐️)", callback_data="buy_boost")]
    ])

    await message.answer(
        "👋 <b>Добро пожаловать на Биржу специалистов!</b>\n\n"
        "Здесь можно быстро найти исполнителя или продвинуть свою анкету в топ.",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "buy_boost")
async def buy_boost_handler(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Premium Boost",
        description="Подъём анкеты в ТОП + выделение на 7 дней",
        payload="premium_boost_7days",
        currency="XTR",
        prices=[LabeledPrice(label="Premium Boost 7 дней", amount=50)],
        provider_token="",
    )
    await callback.answer()


@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    await message.answer(
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        "Ваш профиль теперь в <b>ТОПЕ</b> на 7 дней 🎉"
    )


# ========================= API =========================

@app.get("/api/search")
async def search_candidates(
    skill: Optional[str] = Query(None, description="Поиск по навыку"),
    city: Optional[str] = Query(None),
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
):
    results = users_db.copy()

    # Фильтрация
    if skill:
        skill_lower = skill.lower()
        results = [
            user for user in results
            if any(skill_lower in s.lower() for s in user.skills)
        ]

    if city:
        city_lower = city.lower()
results = [user for user in results if city_lower in user.city.lower()]

    if min_price is not None:
        results = [user for user in results if user.price >= min_price]
    if max_price is not None:
        results = [user for user in results if user.price <= max_price]

    # Сортировка: Премиум сначала, затем по цене (убывание)
    results.sort(key=lambda x: (x.is_premium, x.price), reverse=True)

    return results


@app.get("/")
async def root():
    return {"status": "running", "service": "Job Exchange Bot + Mini App"}


# ========================= ЗАПУСК =========================

async def main():
    port = int(os.getenv("PORT", 8000))
    
    # Запускаем FastAPI и aiogram одновременно
    web_server = asyncio.create_task(
        asyncio.to_thread(
            lambda: __import__("uvicorn").run(
                app, 
                host="0.0.0.0", 
                port=port, 
                log_level="info"
            )
        )
    )

    logger.info(f"🚀 Бот и сервер запущены | Порт: {port}")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if name == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
