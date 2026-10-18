#!/usr/bin/env python3
import os
import argparse
import uuid
import json
from dotenv import load_dotenv
from app import db as _db
from app.notifier import Notifier
from app.football_api import FootballAPI, FootballAPIError
from app.evaluator import evaluate_prediction

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__),'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--init-db', action='store_true')
args = parser.parse_args()

if args.init_db:
    print('Initializing database...')
    _db.init_db()
    print('Done.')
    exit(0)

# Minimal Telegram bot handlers using python-telegram-bot
from telegram.ext import Updater, CommandHandler

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    print('No TELEGRAM_TOKEN in environment. Run with --init-db to only initialize DB.')

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    text = 'Salam! Mən Qol Ovçusuyam. /help yazın.'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def help_cmd(update, context):
    text = ('Əmrlər:\n'
            '/live — canlı oyunları göstər\n'
            '/prematch — yaxın oyunlar\n'
            '/predictions — güclü proqnozlar\n'
            '/results — qiymətləndirilmiş nəticələr\n'
            '/stats — ümumi statistikalar\n'
            '/daily /weekly /monthly — hesabatlar\n'
            '/alerts on/off — bildirişləri aç/bağla')
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def live(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Canlı oyunlar funksiyası hələ hazır deyil — gələcəkdə əlavə olunacaq.')

def prematch(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Oyunöncəsi analiz funksiyası hələ hazırlanır.')

def predictions(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Proqnozlar: hələ ilkin versiya.')

def results(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Qiymətləndirilmiş nəticələr üçün DB inteqrasiyası aktiv deyil.')

def stats(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Statistika modulu hazırlıqda.')

def daily_cmd(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Gündəlik hesabat dərhal əlavə ediləcək.')

def alerts_on(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Alerts ON — qəbul edildi (temp).')

def alerts_off(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Alerts OFF — qəbul edildi (temp).')

# register handlers
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help_cmd))
dispatcher.add_handler(CommandHandler('live', live))
dispatcher.add_handler(CommandHandler('prematch', prematch))
dispatcher.add_handler(CommandHandler('predictions', predictions))
dispatcher.add_handler(CommandHandler('results', results))
dispatcher.add_handler(CommandHandler('stats', stats))
dispatcher.add_handler(CommandHandler('daily', daily_cmd))
dispatcher.add_handler(CommandHandler('alerts', alerts_on))
dispatcher.add_handler(CommandHandler('alerts', alerts_off))

print('Bot starting...')
updater.start_polling()
updater.idle()
