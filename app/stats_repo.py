import os
import json
from typing import List
from dotenv import load_dotenv
from app.football_api import FootballAPI

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

SENT_FILE = os.path.join(DATA_DIR, 'sent_predictions.json')

class StatsRepo:
    """
    Minimal stats repository that fetches recent fixtures for a team using FootballAPI.
    Provides get_recent_goals_for and get_recent_goals_against. Returns lists of goals scored/conceded.
    If API key not configured or provider fails, returns empty lists.
    """
    def __init__(self, api: FootballAPI):
        self.api = api

    def _safe_fetch_team_fixtures(self, team_id: int, limit: int = 8, home_away: str = 'all') -> List[dict]:
        if not self.api or not getattr(self.api, 'key', None):
            return []
        try:
            # api-football supports 'team' and 'last' params
            resp = self.api.fetch_fixtures_paginated('https://api-football-v1.p.rapidapi.com/v3/fixtures', params={'team': team_id, 'last': limit})
            # resp is list of fixtures
            if not isinstance(resp, list):
                # some providers return {'response': [...]} earlier normalized; handle both
                resp = resp.get('response') if isinstance(resp, dict) else []
            # filter by home/away if requested
            fixtures = []
            for f in resp:
                # fixture structure varies; try to extract teams and scores
                try:
                    fixture = f.get('fixture') if isinstance(f, dict) and 'fixture' in f else f
                    teams = f.get('teams') if isinstance(f, dict) and 'teams' in f else f.get('teams', {}) if isinstance(f, dict) else {}
                except Exception:
                    fixture = f
                    teams = {}
                # include raw fixture
                fixtures.append(f)
            return fixtures[:limit]
        except Exception:
            return []

    def get_recent_goals_for(self, team_id: int, limit: int = 8, home_away: str = 'all'):
        fixtures = self._safe_fetch_team_fixtures(team_id, limit=limit, home_away=home_away)
        goals = []
        for f in fixtures:
            try:
                # depending on provider shape
                score = None
                if 'score' in f and isinstance(f['score'], dict):
                    # api-football nested
                    home = f.get('teams', {}).get('home', {})
                    away = f.get('teams', {}).get('away', {})
                    goals_home = f.get('goals', {}).get('home') or f.get('score', {}).get('fulltime', {}).get('home')
                # try multiple shapes
                if isinstance(f, dict):
                    # api-football: f['goals'] sometimes present
                    goals_home = None
                    goals_away = None
                    if 'goals' in f and isinstance(f['goals'], dict):
                        goals_home = f['goals'].get('home')
                        goals_away = f['goals'].get('away')
                    else:
                        # try nested
                        if 'score' in f and isinstance(f['score'], dict):
                            ft = f['score'].get('fulltime') or f['score'].get('full')
                            if isinstance(ft, dict):
                                goals_home = ft.get('home')
                                goals_away = ft.get('away')
                    teams = f.get('teams') or {}
                    home_id = teams.get('home', {}).get('id') if isinstance(teams, dict) else None
                    away_id = teams.get('away', {}).get('id') if isinstance(teams, dict) else None
                    if home_id == team_id:
                        if goals_home is not None:
                            goals.append(goals_home)
                    elif away_id == team_id:
                        if goals_away is not None:
                            goals.append(goals_away)
            except Exception:
                continue
        return goals

    def get_recent_goals_against(self, team_id: int, limit: int = 8, home_away: str = 'all'):
        fixtures = self._safe_fetch_team_fixtures(team_id, limit=limit, home_away=home_away)
        goals = []
        for f in fixtures:
            try:
                goals_home = None
                goals_away = None
                if 'goals' in f and isinstance(f['goals'], dict):
                    goals_home = f['goals'].get('home')
                    goals_away = f['goals'].get('away')
                else:
                    if 'score' in f and isinstance(f['score'], dict):
                        ft = f['score'].get('fulltime') or f['score'].get('full')
                        if isinstance(ft, dict):
                            goals_home = ft.get('home')
                            goals_away = ft.get('away')
                teams = f.get('teams') or {}
                home_id = teams.get('home', {}).get('id') if isinstance(teams, dict) else None
                away_id = teams.get('away', {}).get('id') if isinstance(teams, dict) else None
                if home_id == team_id:
                    if goals_away is not None:
                        goals.append(goals_away)
                elif away_id == team_id:
                    if goals_home is not None:
                        goals.append(goals_home)
            except Exception:
                continue
        return goals

    # Sent predictions tracking
    def has_prediction_been_sent(self, match_id: int, market: str, selection: str) -> bool:
        try:
            if not os.path.exists(SENT_FILE):
                return False
            with open(SENT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return False
        key = f"{match_id}:{market}:{selection}"
        return key in data

    def mark_prediction_sent(self, match_id: int, market: str, selection: str):
        try:
            data = {}
            if os.path.exists(SENT_FILE):
                with open(SENT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            key = f"{match_id}:{market}:{selection}"
            data[key] = True
            with open(SENT_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            pass
