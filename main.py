

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен. Используй /today")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.football-data.org/v4/matches"

    r = requests.get(url, headers=HEADERS)
    data = r.json()

    matches = data.get("matches", [])

    if not matches:
        await update.message.reply_text("Нет матчей сегодня")
        return

    text = "Матчи сегодня:\n\n"

    for m in matches[:15]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        comp = m["competition"]["name"]

        text += f"{comp}\n{home} vs {away}\n\n"

    await update.message.reply_text(text)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    parts = text.split("\n")

    if len(parts) < 3:
        await update.message.reply_text(
            "Формат:\n\nСсылка\nРынок\nКоэффициент"
        )
        return

    market = parts[1].strip()

    try:
        odds = float(parts[2].strip())
    except:
        await update.message.reply_text("Неверный коэффициент")
        return

    if "ТБ 2.5" in market:
        probability = 55
    elif "ТМ 2.5" in market:
        probability = 53
    elif "П1" in market:
        probability = 58
    elif "П2" in market:
        probability = 42
    else:
        probability = 50

    fair_odds = round(100 / probability, 2)
    ev = round((probability / 100 * odds - 1) * 100, 2)

    kelly = ((odds * probability / 100) - 1) / (odds - 1)

    if kelly < 0:
        kelly = 0

    stake_percent = round(kelly * 25, 2)

    if ev > 5:
        verdict = "✅ VALUE BET"
    elif ev > 0:
        verdict = "⚠️ Небольшой перевес"
    else:
        verdict = "❌ Нет валуя"

    answer = (
        f"Рынок: {market}\n"
        f"Коэффициент: {odds}\n\n"
        f"Вероятность: {probability}%\n"
        f"Справедливый кэф: {fair_odds}\n"
        f"EV: {ev}%\n\n"
        f"{verdict}"
    )

    await update.message.reply_text(answer)

         

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, analyze)
    )

    app.run_polling()

if __name__ == "__main__":
    main()