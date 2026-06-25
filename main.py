#

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
results = {
    "wins": 0,
    "losses": 0,
    "profit": 0
}
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
    match_name = parts[0].strip()
    market = parts[1].strip()

    try:
        odds = float(parts[2].strip())
    except:
        await update.message.reply_text("Неверный коэффициент")
        return

    book_probability = 100 / odds

    if "П1" in market:
        probability = book_probability + 3

    elif "П2" in market:
        probability = book_probability + 2

    elif "1Х" in market:
        probability = book_probability + 2

    elif "Х2" in market:
        probability = book_probability + 2

    elif "12" in market:
        probability = book_probability + 2

    elif "ТБ 1.5" in market:
        probability = book_probability + 4

    elif "ТМ 1.5" in market:
        probability = book_probability + 4

    elif "ТБ 2.5" in market:
        probability = book_probability + 3

    elif "ТМ 2.5" in market:
        probability = book_probability + 3

    elif "ТБ 3.5" in market:
        probability = book_probability + 2

    elif "ТМ 3.5" in market:
        probability = book_probability + 2

    elif "ОЗ Да" in market:
        book_probability = 100 / odds

    if "П1" in market:
        probability = book_probability + 3

    elif "П2" in market:
        probability = book_probability + 2

    elif "1Х" in market:
        probability = book_probability + 2

    elif "Х2" in market:
        probability = book_probability + 2

    elif "12" in market:
        probability = book_probability + 2

    elif "ТБ 1.5" in market:
        probability = book_probability + 4

    elif "ТМ 1.5" in market:
        probability = book_probability + 4

    elif "ТБ 2.5" in market:
        probability = book_probability + 3

    elif "ТМ 2.5" in market:
        probability = book_probability + 3

    elif "ТБ 3.5" in market:
        probability = book_probability + 2

    elif "ТМ 3.5" in market:
        probability = book_probability + 2

    elif "ОЗ Да" in market:
        probability = book_probability + 2

    elif "ОЗ Нет" in market:
        probability = book_probability + 2

    else:
        probability = book_probability

    probability = round(min(probability, 95), 1)

    fair_odds = round(100 / probability, 2)
    ev = round((probability / 100 * odds - 1) * 100, 2)

    kelly = ((odds * probability / 100) - 1) / (odds - 1)

    if kelly < 0:
        kelly = 0

    stake_percent = round(kelly * 25, 2)

    if ev >= 10:
        verdict = "🔥 Сильный валуй"
    elif ev >= 5:
        verdict = "✅ VALUE BET"
    elif ev >= 2:
        verdict = "⚠️ Небольшой валуй"
    elif ev >= 0:
        verdict = "➖ Почти по линии"
    else:
        verdict = "❌ Нет валуя"
    answer = (
        f"Матч: {match_name}\n\n"
        f"Рынок: {market}\n"
        f"Коэффициент: {odds}\n\n"
        f"Вероятность: {probability}%\n"
        f"Справедливый кэф: {fair_odds}\n"
        f"EV: {ev}%\n\n"
        f"{verdict}\n\n"
        f"Размер ставки: {stake_percent}% банка"
    )

    await update.message.reply_text(answer)

         
async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):

    results["wins"] += 1

    try:
        odds = float(context.args[0])
        results["profit"] += odds - 1
    except:
        results["profit"] += 1

    await update.message.reply_text("✅ Победа записана")

async def loss(update: Update, context: ContextTypes.DEFAULT_TYPE):

    results["losses"] += 1
    results["profit"] -= 1

    await update.message.reply_text("❌ Поражение записано")
    
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = results["wins"] + results["losses"]

    if total == 0:
        await update.message.reply_text("Статистика пока пустая")
        return

    winrate = round(results["wins"] / total * 100, 2)
    roi = round(results["profit"] / total * 100, 2)
    text = (
        f"Ставок: {total}\n"
        f"Побед: {results['wins']}\n"
        f"Поражений: {results['losses']}\n"
        f"Winrate: {winrate}%\n\n"
        f"Прибыль: {round(results['profit'],2)} unit\n"
        f"ROI: {roi}%"
)

    await update.message.reply_text(text)
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, analyze)
    )

    app.run_polling()

if __name__ == "__main__":
    main()