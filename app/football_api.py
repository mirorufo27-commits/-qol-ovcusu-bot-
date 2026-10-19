import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FOOTBALL_API_KEY")
PROVIDER = os.getenv("FOOTBALL_API_PROVIDER", "football-data.org")

class FootballAPIError(Exception):
    pass

class FootballAPI:
    def __init__(self, provider=PROVIDER, api_key=API_KEY):
        self.key = api_key
        self.provider = provider

    def _request_with_retries(self, url, headers=None, params=None, max_retries=3):
        if not self.key:
            raise FootballAPIError("FOOTBALL_API_KEY konfiqurasiya edilməyib.")
        request_headers = dict(headers or {})
        if self.provider == "football-data.org":
            request_headers["X-Auth-Token"] = self.key
        for attempt in range(max_retries):
            try:
                r = requests.get(url, headers=request_headers, params=params or {}, timeout=15)
                if r.status_code == 429:
                    if attempt + 1 < max_retries:
                        try:
                            wait = min(3, max(1, int(r.headers.get("Retry-After", "1"))))
                        except ValueError:
                            wait = 1
                        time.sleep(wait)
                        continue
                    raise FootballAPIError("API sorğu limiti dolub (429).")
                if r.status_code == 403:
                    raise FootballAPIError("API 403: yarışma planınızda əlçatan olmaya bilər.")
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                if attempt + 1 == max_retries:
                    raise FootballAPIError(f"API sorğusu alınmadı: {e}") from e
                time.sleep(0.5 * (attempt + 1))
        raise FootballAPIError("API sorğusu uğursuz oldu.")

    def fetch_fixtures_paginated(self, endpoint_url, params=None):
        params = dict(params or {})
        if self.provider == "football-data.org":
            data = self._request_with_retries(endpoint_url, params=params)
            return data.get("matches", [])
        page = 1
        items_all = []
        while True:
            data = self._request_with_retries(endpoint_url, params={**params, "page": page})
            items = data.get("response") or data.get("data") or []
            if not items:
                break
            items_all.extend(items)
            paging = data.get("paging") or {}
            if paging and paging.get("current") >= paging.get("total", page):
                break
            page += 1
        return items_all

    def get_match(self, match_id):
        if not self.key:
            raise FootballAPIError("FOOTBALL_API_KEY konfiqurasiya edilməyib.")
        if self.provider == "football-data.org":
            return self._request_with_retries(f"https://api.football-data.org/v4/matches/{match_id}")
        return self._request_with_retries(
            "https://api-football-v1.p.rapidapi.com/v3/fixtures",
            headers={
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
                "x-rapidapi-key": self.key,
            },
            params={"id": match_id},
        )

    def get_fixture_stats(self, match_id):
        try:
            data = self.get_match(match_id)
            if self.provider == "football-data.org":
                return data
            response = data.get("response") or data.get("data") or []
            return response[0] if response else data
        except FootballAPIError as e:
            print(f"Oyun statistikası alınmadı: {e}")
            return None
