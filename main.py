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

    url = parts[0].strip()
    market = parts[1].strip()
    odds = parts[2].strip()

    answer = (
        f"Ссылка получена:\n{url}\n\n"
        f"Рынок:\n{market}\n\n"
        f"Коэффициент:\n{odds}"
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