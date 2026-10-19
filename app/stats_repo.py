import json
import os
from typing import List
from datetime import date, timedelta

from dotenv import load_dotenv
from app.football_api import FootballAPI

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
SENT_FILE = os.path.join(DATA_DIR, 'sent_predictions.json')

FINISHED_STATUSES = {'FT', 'AET', 'PEN', 'FINISHED'}


class StatsRepo:
    """Fetch completed team fixtures and extract reliable goal statistics."""

    def __init__(self, api: FootballAPI):
        self.api = api
        self._team_fixture_cache = {}

    @staticmethod
    def _fixture_data(match):
        if not isinstance(match, dict):
            return {}, {}, None, None, None

        # football-data.org formatı
        if "homeTeam" in match or "utcDate" in match:
            teams = {
                "home": match.get("homeTeam") or {},
                "away": match.get("awayTeam") or {},
            }
            fixture = {"date": match.get("utcDate")}
            score = match.get("score") or {}
            fulltime = score.get("fullTime") or {}
            return (
                teams,
                fixture,
                match.get("status"),
                fulltime.get("home"),
                fulltime.get("away"),
            )

        # Köhnə API-Football formatı
        fixture = match.get("fixture") or {}
        teams = match.get("teams") or {}
        goals = match.get("goals") or {}
        score = match.get("score") or {}
        fulltime = score.get("fulltime") or score.get("full") or {}
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        if home_goals is None:
            home_goals = fulltime.get("home")
        if away_goals is None:
            away_goals = fulltime.get("away")
        status = (fixture.get("status") or {}).get("short")
        return teams, fixture, status, home_goals, away_goals

    @classmethod
    def _is_finished(cls, match):
        teams, fixture, status, home_goals, away_goals = cls._fixture_data(match)
        if home_goals is None or away_goals is None:
            return False
        if status is not None:
            return status in FINISHED_STATUSES
        return True

    def _safe_fetch_team_fixtures(
        self, team_id: int, limit: int = 8, home_away: str = 'all'
    ) -> List[dict]:
        cache_key = (team_id, limit, home_away)
        if cache_key not in self._team_fixture_cache:
            self._team_fixture_cache[cache_key] = self._fetch_team_fixtures_uncached(
                team_id, limit, home_away
            )
        return self._team_fixture_cache[cache_key]

    def _fetch_team_fixtures_uncached(
        self, team_id: int, limit: int = 8, home_away: str = 'all'
    ) -> List[dict]:
        if not self.api or not getattr(self.api, 'key', None):
            return []
        if home_away not in ('all', 'home', 'away'):
            return []

        try:
            requested = max(limit * 3, limit)
            if getattr(self.api, "provider", "") == "football-data.org":
                url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
                today = date.today()
                date_from = (today - timedelta(days=730)).isoformat()
                date_to = today.isoformat()
                response = self.api.fetch_fixtures_paginated(
                    url,
                    params={"status": "FINISHED", "dateFrom": date_from, "dateTo": date_to, "limit": 100},
                )
            else:
                url = 'https://api-football-v1.p.rapidapi.com/v3/fixtures'
                response = self.api.fetch_fixtures_paginated(
                    url, params={'team': team_id, 'last': requested}
                )

            if isinstance(response, dict):
                response = response.get('matches') or response.get('response') or []
            if not isinstance(response, list):
                return []

            fixtures = []
            for match in response:
                if not isinstance(match, dict) or not self._is_finished(match):
                    continue

                teams, _, _, _, _ = self._fixture_data(match)
                home = teams.get('home') or {}
                away = teams.get('away') or {}
                home_id = home.get('id')
                away_id = away.get('id')

                if home_away == 'home' and home_id != team_id:
                    continue
                if home_away == 'away' and away_id != team_id:
                    continue
                if home_id != team_id and away_id != team_id:
                    continue

                fixtures.append(match)
                if len(fixtures) >= limit:
                    break

            return fixtures
        except Exception as exc:
            print(f'StatsRepo fixture fetch error: {exc}')
            return []

    def get_recent_goals_for(
        self, team_id: int, limit: int = 8, home_away: str = 'all'
    ):
        goals = []
        for match in self._safe_fetch_team_fixtures(team_id, limit, home_away):
            teams, _, _, home_goals, away_goals = self._fixture_data(match)
            home_id = (teams.get('home') or {}).get('id')
            away_id = (teams.get('away') or {}).get('id')

            if home_id == team_id:
                goals.append(home_goals)
            elif away_id == team_id:
                goals.append(away_goals)

        return goals

    def get_recent_goals_against(
        self, team_id: int, limit: int = 8, home_away: str = 'all'
    ):
        goals = []
        for match in self._safe_fetch_team_fixtures(team_id, limit, home_away):
            teams, _, _, home_goals, away_goals = self._fixture_data(match)
            home_id = (teams.get('home') or {}).get('id')
            away_id = (teams.get('away') or {}).get('id')

            if home_id == team_id:
                goals.append(away_goals)
            elif away_id == team_id:
                goals.append(home_goals)

        return goals

    def has_prediction_been_sent(
        self, match_id: int, market: str, selection: str
    ) -> bool:
        try:
            with open(SENT_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (OSError, ValueError):
            return False

        return f'{match_id}:{market}:{selection}' in data

    def mark_prediction_sent(
        self, match_id: int, market: str, selection: str
    ):
        try:
            data = {}
            if os.path.exists(SENT_FILE):
                with open(SENT_FILE, 'r', encoding='utf-8') as file:
                    data = json.load(file)

            data[f'{match_id}:{market}:{selection}'] = True
            with open(SENT_FILE, 'w', encoding='utf-8') as file:
                json.dump(data, file)
        except (OSError, ValueError) as exc:
            print(f'Could not save sent prediction: {exc}')
