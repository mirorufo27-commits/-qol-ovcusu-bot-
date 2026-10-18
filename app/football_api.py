import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('FOOTBALL_API_KEY')
PROVIDER = os.getenv('FOOTBALL_API_PROVIDER', 'api-football')

DEFAULT_HEADERS = {}
if API_KEY:
    DEFAULT_HEADERS = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': API_KEY
    }

class FootballAPIError(Exception):
    pass

class FootballAPI:
    def __init__(self, provider=PROVIDER, api_key=API_KEY):
        self.key = api_key
        self.provider = provider

    def _request_with_retries(self, url, headers=None, params=None, max_retries=5):
        headers = headers or DEFAULT_HEADERS
        params = params or {}
        for attempt in range(1, max_retries + 1):
            try:
                r = requests.get(url, headers=headers, params=params, timeout=10)
                if r.status_code == 429:
                    retry_after = r.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait = int(retry_after)
                        except Exception:
                            wait = min(60, (2 ** (attempt - 1)))
                    else:
                        wait = min(60, (2 ** (attempt - 1)))
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                if attempt == max_retries:
                    raise FootballAPIError(f'Request failed after {max_retries} attempts: {e}')
                backoff = (2 ** (attempt - 1)) * 0.5
                time.sleep(backoff)
        raise FootballAPIError('Unreachable code in _request_with_retries')

    def fetch_fixtures_paginated(self, endpoint_url, params=None):
        params = params.copy() if params else {}
        page = 1
        all_items = []
        while True:
            params.update({'page': page})
            data = self._request_with_retries(endpoint_url, headers=DEFAULT_HEADERS, params=params)
            items = data.get('response') or data.get('data') or data.get('matches') or []
            if not items:
                break
            # normalize items if necessary
            all_items.extend(items)
            meta = data.get('meta') or data.get('paging') or {}
            if meta:
                current = meta.get('current_page') or meta.get('page') or page
                last = meta.get('last_page') or meta.get('total_pages')
                if last and current >= last:
                    break
            links = data.get('links') or {}
            if links and not links.get('next'):
                break
            page += 1
        return all_items

    def get_match(self, match_id):
        """
        Fetch fixture information for a match id using the configured provider.
        Returns parsed JSON response or raises FootballAPIError.
        """
        if not self.key:
            raise FootballAPIError('FOOTBALL_API_KEY not configured')

        if self.provider == 'api-football':
            url = 'https://api-football-v1.p.rapidapi.com/v3/fixtures'
            params = {'id': match_id}
            return self._request_with_retries(url, headers=DEFAULT_HEADERS, params=params)

        raise FootballAPIError(f'Unsupported provider: {self.provider}')

    def get_fixture_stats(self, match_id):
        """
        Attempt to fetch fixture statistics (corners, shots, etc.) if provider supports it.
        Uses the same request-with-retries mechanism and cautiously extracts stats.
        """
        try:
            data = self.get_match(match_id)
            # Common API responses wrap items under 'response' which is a list
            resp = data.get('response') or data.get('data') or []
            if isinstance(resp, list) and len(resp) > 0:
                first = resp[0]
                # api-football may include 'statistics' or 'stats' inside the fixture object
                stats = first.get('statistics') or first.get('stats') or first.get('score') or None
                # also include aggregated keys if present
                if not stats:
                    # sometimes the provider includes more detailed structure
                    # fall back to returning the whole fixture object for caller parsing
                    return first
                return stats
            # fallback to raw data
            return data
        except FootballAPIError:
            return None
