
import logging

from telegram import ReplyKeyboardMarkup
# from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
#                           ConversationHandler, PicklePersistence,StringRegexHandler)

from config import TOKEN
from telebot import TeleBot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import game_collection
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


bot = TeleBot(TOKEN)

TABOO_WORD = "Eldar"

botUser = bot.get_me()


    
def func():
    print("Test")


def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Join", callback_data="join") )
    return markup



team1 = []
team2 = []

players = []

def user_object(user):
    return {"id" : user.id, "username": user.username}


@bot.message_handler(commands=['game'])
def game(msg):
    bot.send_message(msg.chat.id,"Team1 : \nTeam2 :",parse_mode='MarkdownV2',reply_markup=gen_markup())
    
    
    
    

@bot.message_handler(func=lambda msg: msg.chat.type == 'private', commands=['start'])
def start_command(msg,*args,**kwargs):
    user = user_object(msg.from_user)
    
    if user not in players:
        players.append(user)
        game_collection.update_one(
            {
                'user_id' : user['id']
            },
            {
                '$set' : { 'isInGame' : True }
            }
        )

        bot.reply_to(msg,"You have been added to game :)")
    else:
        bot.reply_to(msg,"You are already in the game!")
    



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    userID = call.from_user.id
    if call.data == 'join':
        bot.answer_callback_query(call.id,url="t.me/{}?start=start".format(botUser.username),cache_time=1)
        data = {'chat_id' : call.message.chat.id,'user_id' : userID, 'isInGame' : False}
        found = False

        for _ in game_collection.find({'user_id' : userID }) :
            found = True

        if found == False :
            game_collection.insert_one(data)
    







bot.polling()