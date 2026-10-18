import os
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('FOOTBALL_API_KEY')
PROVIDER = os.getenv('FOOTBALL_API_PROVIDER','')

class FootballAPIError(Exception):
    pass

class FootballAPI:
    def __init__(self):
        self.key = API_KEY
        self.provider = PROVIDER

    def get_match(self, match_id):
        # Provider-specific implementation placeholder
        if not self.key:
            raise FootballAPIError('FOOTBALL_API_KEY not configured')
        # Example for api-football (user must configure)
        if self.provider == 'api-football' or True:
            url = f'https://api-football-v1.p.rapidapi.com/v3/fixtures?id={match_id}'
            headers = {
                'x-rapidapi-key': self.key,
                'x-rapidapi-host': 'api-football-v1.p.rapidapi.com'
            }
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 403:
                raise FootballAPIError('Access denied or invalid key')
            else:
                raise FootballAPIError(f'HTTP {r.status_code}')

    def get_fixture_stats(self, match_id):
        # attempt to return stats (corners, shots, etc) if provider supports
        try:
            data = self.get_match(match_id)
            # Parse cautiously
            return data
        except FootballAPIError:
            return None
