
import logging

from telegram import ReplyKeyboardMarkup
# from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
#                           ConversationHandler, PicklePersistence,StringRegexHandler)

from config import TOKEN
from telebot import TeleBot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (game_collection, markup_message_collection)
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


bot = TeleBot(TOKEN)


botUser = bot.get_me()




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
    message = bot.send_message(msg.chat.id,"Join to the game",parse_mode='MarkdownV2',reply_markup=gen_markup())
    data = {'chat_id' : msg.chat.id, 'markup_message_id': message.message_id }
    markup_message_collection.insert_one(data)
    

def get_joined_users(chatID):
    game = game_collection.find({'chat_id': chatID,'isInGame' : True})
    joiners = []
    for joiner in game:
        data = {'user_id' : joiner['user_id'], 'username' : joiner['username']}
        joiners.append(data)
    return joiners

# On success returns True   
    
def edit_markup_message(userID):
    game = game_collection.find_one({'user_id': userID})
    
    try:
        chatID = game['chat_id']
        markup_message = markup_message_collection.find_one({'chat_id' : chatID})
        try:
            markup_messageID = markup_message['markup_message_id']
            
            joined_users_id = get_joined_users(chatID)

            information = "Players: "
            for data in joined_users_id :
                information = " " + information + "["+ data['username'] +"](tg://user?id=" + str(data['user_id']) + ")"
            
            bot.edit_message_text(information,
                                    chat_id=chatID,
                                    message_id=markup_messageID,
                                    reply_markup=gen_markup(),
                                    parse_mode="MarkdownV2"
                                    )
        except KeyError:
            print("Key error ")
        
    except KeyError :
        print("Key error!")
    



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
        edit_markup_message(user['id'])
        bot.reply_to(msg,"You have been added to game :)")
    else:
        bot.reply_to(msg,"You are already in the game!")
    



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    userID = call.from_user.id
    username = call.from_user.username
    if call.data == 'join':
        bot.answer_callback_query(call.id,url="t.me/{}?start=start".format(botUser.username),cache_time=1)
        data = {'chat_id' : call.message.chat.id,'user_id' : userID, 'username' : username ,'isInGame' : False}
        found = False
        # Checking user's attendance in any game 
        for _ in game_collection.find({'user_id' : userID }) :
            found = True

        if found == False :
            game_collection.insert_one(data)
    







bot.polling()