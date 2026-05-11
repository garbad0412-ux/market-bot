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
from aiogram.client.default import DefaultBotProperties

# ========================= НАСТРОЙКИ =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not BOT_TOKEN or not WEBAPP_URL:
    raise ValueError("❌ BOT_TOKEN и WEBAPP_URL обязательны!")

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
    UserProfile(id=1, name="Иван Петров", skills=["Python", "FastAPI"], city="Москва", price=2500, is_premium=True, rating=4.9),
    UserProfile(id=2, name="Анна Смирнова", skills=["Figma", "UI/UX"], city="Удалённо", price=1800, is_premium=False, rating=5.0),
    UserProfile(id=3, name="Дмитрий Соколов", skills=["React Native", "Flutter"], city="Санкт-Петербург", price=3200, is_premium=True, rating=4.7),
]

# ========================= ИНИЦИАЛИЗАЦИЯ =========================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
app = FastAPI(title="Биржа Специалистов")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    await message.answer("👋 <b>Добро пожаловать на Биржу Специалистов!</b>", reply_markup=kb)


@dp.callback_query(F.data == "buy_boost")
async def buy_boost_handler(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Premium Boost",
        description="Подъём анкеты в ТОП на 7 дней",
        payload="premium_boost",
        currency="XTR",
        prices=[LabeledPrice(label="Boost 7 дней", amount=50)],
        provider_token="",
    )


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    await message.answer("🎉 <b>Оплата прошла успешно!</b>\nТы теперь
