#!/usr/bin/env python3
import os
import json
import time
import argparse
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from app.football_api import FootballAPI, FootballAPIError
from app.stats_repo import StatsRepo
from app.predictor import match_result_probabilities
from app.evaluator import evaluate_match_for_predictions

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
CACHE_FILE = os.path.join(DATA_DIR, "prematch_cache.json")
CACHE_SECONDS = 900
MAX_MATCHES_TO_ANALYZE = 10
MAX_DISPLAY_PROBABILITY = 0.90

# API-Football league IDs. Names shown to Telegram users are canonical.
LEAGUES = {
    39: "English Premier League",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
    203: "Turkish Super Lig",
    419: "Azerbaijan Premier League",
    88: "Eredivisie",
    94: "Primeira Liga",
    144: "Belgian Pro League",
    179: "Scottish Premiership",
}

DEFAULT_CONFIG = {
    "top_leagues": list(LEAGUES.values()),
    "thresholds": {
        "over25_min_prob": 0.70,
        "btts_min_prob": 0.75,
    },
    "stats": {
        "recent_matches_count": 8,
        "min_matches_required": 6,
        "decay_half_life_matches": 5,
    },
}


def load_config():
    config = DEFAULT_CONFIG.copy()
    try:
        import yaml
        with open("config.yml", "r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
        for key in ("top_leagues", "thresholds", "stats"):
            if isinstance(loaded.get(key), (list, dict)):
                if key == "top_leagues":
                    config[key] = loaded[key]
                else:
                    config[key] = {**config[key], **loaded[key]}
    except ImportError:
        print("PyYAML yoxdur; daxili standart konfiqurasiya istifadə edilir.")
    except Exception as exc:
        print(f"Konfiqurasiya oxunmadı, standart dəyərlər istifadə edilir: {exc}")
    return config


def parse_kickoff(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError):
        return None


def load_cached_fixtures():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            cached = json.load(file)
        if time.time() - cached.get("saved_at", 0) < CACHE_SECONDS:
            return cached.get("fixtures", [])
    except (OSError, ValueError, TypeError):
        pass
    return None


def save_cached_fixtures(fixtures):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(
                {"saved_at": time.time(), "fixtures": fixtures},
                file,
                ensure_ascii=False,
            )
    except (OSError, TypeError) as exc:
        print(f"Oyun keşini saxlamaq mümkün olmadı: {exc}")


def fetch_upcoming_fixtures(api, config):
    cached = load_cached_fixtures()
    if cached:
        return cached

    if not api.key:
        raise FootballAPIError("FOOTBALL_API_KEY konfiqurasiya edilməyib.")

    today = datetime.now().date()
    now = datetime.now(timezone.utc)
    url = "https://api.football-data.org/v4/matches"

    try:
        data = api._request_with_retries(
            url,
            params={
                "dateFrom": today.isoformat(),
                "dateTo": (today + timedelta(days=2)).isoformat(),
            },
            max_retries=3,
        )
    except FootballAPIError as exc:
        print(f"Oyunları alma xətası: {exc}")
        return []

    fixtures_by_id = {}
    priority_codes = {"PL", "CL", "EL", "PD", "BL1", "SA"}

    for item in data.get("matches", []):
        if not isinstance(item, dict):
            continue

        competition = item.get("competition") or {}
        home = item.get("homeTeam") or {}
        away = item.get("awayTeam") or {}
        kickoff_text = item.get("utcDate")
        kickoff = parse_kickoff(kickoff_text)
        status = item.get("status")

        if not item.get("id") or not home.get("id") or not away.get("id"):
            continue
        if kickoff is None or kickoff <= now:
            continue
        if status not in ("SCHEDULED", "TIMED"):
            continue

        code = competition.get("code") or ""
        name = competition.get("name") or "Digər liqa"
        normalized = {
            "fixture_id": item["id"],
            "home_team_id": home["id"],
            "away_team_id": away["id"],
            "home_team": home.get("name") or "Ev komandası",
            "away_team": away.get("name") or "Səfər komandası",
            "league": name,
            "league_code": code,
            "kickoff": kickoff_text,
            "league_priority": 0 if code in priority_codes else 1,
        }
        fixtures_by_id[item["id"]] = normalized

    fixtures = sorted(
        fixtures_by_id.values(),
        key=lambda m: (
            m["league_priority"],
            parse_kickoff(m["kickoff"]) or now,
        ),
    )
    save_cached_fixtures(fixtures)
    print(f"Yaxın 3 gündə tapılan oyun sayı: {len(fixtures)}")
    return fixtures

def build_prediction_message(api, config, repo=None):
    fixtures = fetch_upcoming_fixtures(api, config)
    if not fixtures:
        return (
            "⚽ Oyunöncəsi analiz\n\n"
            "Seçilmiş liqalarda qarşıdakı 3 gün üçün oyun tapılmadı "
            "və ya API məlumatı alınmadı. Bir qədər sonra yenidən yoxla."
        )

    if repo is None:
        repo = StatsRepo(api)
    lines = ["⚽ QOL OVÇUSU — OYUNÖNCƏSİ ANALİZ", ""]
    shown = 0
    analyzed = 0
    insufficient = 0

    for match in fixtures[:MAX_MATCHES_TO_ANALYZE]:
        result = evaluate_match_for_predictions(
            match=match,
            stats_repo=repo,
            league_avg=None,
            config=config,
        )

        if result.get("status") != "ok":
            insufficient += 1
            continue

        analyzed += 1
        selections = [
            ("over25_candidate", "over25_prob", "2.5 ÜST"),
            ("btts_candidate", "btts_prob", "QOL-QOL (BTTS)"),
        ]

        result_probs = match_result_probabilities(
            result.get("lambda_home"),
            result.get("lambda_away"),
        )
        if result_probs:
            result_labels = {
                "home_win": "1 — Ev sahibi qələbəsi",
                "draw": "X — Heç-heçə",
                "away_win": "2 — Səfər qələbəsi",
            }
            best_key = max(result_probs, key=result_probs.get)
            best_probability = result_probs[best_key]
            if 0.40 <= best_probability <= MAX_DISPLAY_PROBABILITY:
                selections.append((
                    "result_candidate",
                    "result_probability",
                    result_labels[best_key],
                ))
                result["result_candidate"] = True
                result["result_probability"] = best_probability
        for candidate_key, probability_key, market_name in selections:
            probability = result.get(probability_key)
            if not result.get(candidate_key) or probability is None:
                continue

            # Very extreme outputs are withheld rather than presented as certainty.
            if probability > MAX_DISPLAY_PROBABILITY:
                continue

            kickoff = parse_kickoff(match.get("kickoff"))
            kickoff_text = kickoff.astimezone().strftime("%d.%m %H:%M") if kickoff else "Vaxt məlum deyil"

            lines.extend([
                f"🏆 {match['league']}",
                f"⚽ {match['home_team']} — {match['away_team']}",
                f"🕒 {kickoff_text}",
                f"🎯 Bazar: {market_name}",
                f"📊 Model ehtimalı: {round(probability * 100)}%",
                "",
            ])
            shown += 1

    if shown == 0:
        return (
            "⚽ QOL OVÇUSU — OYUNÖNCƏSİ ANALİZ\n\n"
            f"Yoxlanılan oyun: {min(len(fixtures), MAX_MATCHES_TO_ANALYZE)}\n"
            f"Kifayət qədər statistikası olmayan: {insufficient}\n\n"
            "Meyarlara uyğun etibarlı seçim tapılmadı. "
            "Ehtimalları süni artırmırıq."
        )

    lines.append(f"Yoxlanılan oyun: {min(len(fixtures), MAX_MATCHES_TO_ANALYZE)}")
    lines.append("Qeyd: ehtimallar model hesablamasıdır, zəmanət deyil.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-db", action="store_true")
    args = parser.parse_args()

    if args.init_db:
        from app import db
        db.init_db()
        print("Database initialization requested.")
        return

    from telegram.ext import Application, CommandHandler

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_TOKEN yoxdur. .env faylını yoxla.")

    api = FootballAPI()
    config = load_config()
    repo = StatsRepo(api)
    application = Application.builder().token(token).build()

    async def start(update, context):
        await update.effective_message.reply_text(
            "Salam! Mən Qol Ovçusuyam ⚽\n"
            "/prematch — oyunöncəsi analiz\n"
            "/predictions — uyğun proqnozlar\n"
            "/help — kömək"
        )

    async def help_cmd(update, context):
        await update.effective_message.reply_text(
            "Əmrlər:\n"
            "/prematch — yaxın oyunları analiz et\n"
            "/predictions — uyğun proqnozları göstər\n\n"
            "Yalnız 2.5 ÜST və QOL-QOL bazarları göstərilir. "
            "Kifayət qədər statistika olmadıqda seçim verilmir."
        )

    async def predictions(update, context):
        message = update.effective_message
        await message.reply_text("Oyunlar və statistikalar yoxlanılır...")
        try:
            output = build_prediction_message(api, config, repo)
        except Exception as exc:
            print(f"Prediction error: {exc}")
            output = (
                "Analiz alınmadı. API açarını, internet bağlantısını "
                "və API limitini yoxla."
            )
        await message.reply_text(output)

    async def live(update, context):
        await update.effective_message.reply_text(
            "Bu bot hazırda yalnız oyunöncəsi analiz üçündür."
        )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("prematch", predictions))
    application.add_handler(CommandHandler("predictions", predictions))
    application.add_handler(CommandHandler("live", live))

    print("Qol Ovçusu botu başladılır...")
    application.run_polling()


if __name__ == "__main__":
    main()
