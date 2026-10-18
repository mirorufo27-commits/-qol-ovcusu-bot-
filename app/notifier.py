import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

class Notifier:
    def __init__(self, token=None):
        self.token = token or TELEGRAM_TOKEN
        if not self.token:
            raise RuntimeError('Telegram token not configured')
        self.bot = Bot(token=self.token)

    def send_result(self, chat_id, prediction, match_result):
        # Build Azerbaijani message
        title = 'QOL OVÇUSU — SİQNAL NƏTİCƏSİ'
        home = match_result.get('home_team')
        away = match_result.get('away_team')
        score = match_result.get('full_time_score') or 'N/A'
        market = prediction.get('market')
        prob = prediction.get('probability')
        status = prediction.get('status')
        lines = [title, '', f'⚽ Oyun: {home} — {away}', f'🏁 Yekun hesab: {score}', f'📊 Bazar: {market}', f'🎯 İlkin ehtimal: {prob}%', f'📌 Nəticə: {status}']
        text = "\n".join(lines)
        # send message
        try:
            self.bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception as e:
            print('Telegram send error', e)
            return False
