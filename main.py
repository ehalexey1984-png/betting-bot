##

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

    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    url = "https://api.football-data.org/v4/matches"

    r = requests.get(url, headers=HEADERS)
    

    
    data = r.json()

    fixtures = data.get("matches", [])

    if not fixtures:
        await update.message.reply_text("Матчей не найдено")
        return

    text = "Ближайшие матчи:\n\n"

    for match in fixtures:

        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        league = match["competition"]["name"]

        text += f"{league}\n{home} - {away}\n\n"

    await update.message.reply_text(text)
async def team(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Использование:\n/team Arsenal")
        return

    name = " ".join(context.args)

    url = f"https://v3.football.api-sports.io/teams?search={name}"

    r = requests.get(url, headers=HEADERS)
    data = r.json()

    response = data.get("response", [])

    if not response:
        await update.message.reply_text("Команда не найдена")
        return

    team = response[0]

    await update.message.reply_text(
        f"ID: {team['team']['id']}\n"
        f"Команда: {team['team']['name']}\n"
        f"Страна: {team['team']['country']}"
    )
async def form(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text(
            "Использование:\n/form Netherlands"
        )
        return

    team_name = " ".join(context.args)

    url = f"https://api.football-data.org/v4/teams?name={team_name}"

    r = requests.get(url, headers=HEADERS)
    data = r.json()

    teams = data.get("teams", [])

    if not teams:
        await update.message.reply_text("Команда не найдена")
        return

    team_id = teams[0]["id"]

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=5"

    r = requests.get(url, headers=HEADERS)
    data = r.json()

    matches = data.get("matches", [])

    text = f"Последние матчи {team_name}:\n\n"

    for m in matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]

        home_score = m["score"]["fullTime"]["home"]
        away_score = m["score"]["fullTime"]["away"]

        text += f"{home} {home_score}:{away_score} {away}\n"

    await update.message.reply_text(text)
def get_team_id(team_name):

    url = "https://api.football-data.org/v4/teams"

    r = requests.get(url, headers=HEADERS)
    data = r.json()

    teams = data.get("teams", [])

    for team in teams:
        if team["name"].lower() == team_name.lower():
            return team["id"]

    return None


def get_last5(team_id):

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=5"

    r = requests.get(url, headers=HEADERS)
    data = r.json()

    return data.get("matches", [])
def calculate_form(matches, team_id):

    wins = 0
    draws = 0
    losses = 0

    goals_for = 0
    goals_against = 0

    for m in matches:

        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]

        home_goals = m["score"]["fullTime"]["home"]
        away_goals = m["score"]["fullTime"]["away"]

        if home_goals is None or away_goals is None:
            continue

        team_is_home = m["homeTeam"]["id"] == team_id

        if team_is_home:

            gf = home_goals
            ga = away_goals

        else:

            gf = away_goals
            ga = home_goals

        goals_for += gf
        goals_against += ga

        if gf > ga:
            wins += 1
        elif gf == ga:
            draws += 1
        else:
            losses += 1

    return {
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "gf": goals_for,
        "ga": goals_against
    }
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    parts = text.split("\n")

    if len(parts) < 4:
        await update.message.reply_text(
            "Формат:\n\nКоманда 1\nКоманда 2\nРынок\nКоэффициент"
        )
        return

    home_team = parts[0].strip()
    away_team = parts[1].strip()
    market = parts[2].strip()

    try:
        odds = float(parts[3].strip())
    except:
        await update.message.reply_text("Неверный коэффициент")
        return

    home_id = get_team_id(home_team)
    away_id = get_team_id(away_team)

    if home_id is None or away_id is None:
        await update.message.reply_text("Не удалось найти одну из команд")
        return

    home_matches = get_last5(home_id)
    away_matches = get_last5(away_id)

    home_form = calculate_form(home_matches, home_id)
    away_form = calculate_form(away_matches, away_id)

    book_probability = 100 / odds

    home_points = home_form["wins"] * 3 + home_form["draws"]
    away_points = away_form["wins"] * 3 + away_form["draws"]

    home_strength = home_points + (home_form["gf"] - home_form["ga"])
    away_strength = away_points + (away_form["gf"] - away_form["ga"])

    if "П1" in market:

        total = home_strength + away_strength

        if total == 0:
            probability = book_probability
        else:
            probability = home_strength / total * 100

    elif "П2" in market:

        total = home_strength + away_strength

        if total == 0:
            probability = book_probability
        else:
            probability = away_strength / total * 100

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
        f"Матч: {home_team} - {away_team}\n\n"
        f"Форма:\n"
        f"{home_team}: {home_form['wins']}-{home_form['draws']}-{home_form['losses']} "
        f"({home_form['gf']}:{home_form['ga']})\n"
        f"{away_team}: {away_form['wins']}-{away_form['draws']}-{away_form['losses']} "
        f"({away_form['gf']}:{away_form['ga']})\n\n"
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
    app.add_handler(CommandHandler("form", form))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("team", team))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, analyze)
    )

    app.run_polling()

if __name__ == "__main__":
    main()