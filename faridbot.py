
import logging


from config import TOKEN
from telebot import TeleBot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (game_collection, markup_message_collection, current_plays_collection, words_collection)
from states import States
from datetime import datetime,timedelta

import json
import numpy as np
import random



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
    global players
    players = []
    game_collection.delete_one({"chat_id" : msg.chat.id})
    message = bot.send_message(msg.chat.id,"Join to the game",parse_mode='MarkdownV2',reply_markup=gen_markup())
    data = {'chat_id' : msg.chat.id, 'markup_message_id': message.message_id ,'current_state' : States.T_GAME}
    game_collection.insert_one(data)
    

def get_current_state(chatID):
    result = game_collection.find_one({'chat_id' : { '$exists': True, '$ne': 'null' } })
    if result :
        chat = game_collection.find_one({"chat_id" : chatID})
        current_state = chat["current_state"]
        return current_state
    

def get_joined_users(chatID):
    game = game_collection.find_one({'chat_id': chatID,'info.isInGame' : True})
    
    joiners = []
    for joiner in game['info']:
        data = {'user_id' : joiner['user_id'], 'username' : joiner['username']}
        joiners.append(data)
    return joiners

# On success returns True   
    
def edit_markup_message(userID):
    game = game_collection.find_one({'info.user_id': userID})
    
    try:
        chatID = game['chat_id']
        markup_message = game_collection.find_one({'chat_id' : chatID})
        try:
            markup_messageID = markup_message['markup_message_id']
            
            joined_users_id = get_joined_users(chatID)

            information = "Players: "
            for data in joined_users_id :
                information = " " + information + "["+ data['username'] +"](tg://user?id=" + str(data['user_id']) + ") " 
            
            bot.edit_message_text(information,
                                    chat_id=chatID,
                                    message_id=markup_messageID,
                                    reply_markup=gen_markup(),
                                    parse_mode="MarkdownV2"
                                    )
        except KeyError as e:
            print("Key error" + str(e))
        
    except KeyError :
        print("Key error!")




@bot.message_handler(func=lambda msg: msg.chat.type == 'private', commands=['start'])
def start_command(msg,*args,**kwargs):
    user = user_object(msg.from_user)
    result = game_collection.find_one({"info.user_id" : user['id'] , 'info.isInGame' : { '$exists': True, '$ne': 'null' } })
    
    
    
    if user not in players and result:
        game_collection.update_one(
            {
                'info.user_id' : user['id']
            },
            {
                '$set' : { 'info.$.isInGame' : True , 'info.$.private_chat_id' : msg.chat.id }
            }
        )
        edit_markup_message(user['id'])
        bot.reply_to(msg,"You have been added to game :)")
        players.append(user)
    else:
        bot.reply_to(msg,"You are already in the game!")
    

@bot.message_handler(commands=['stop'])
def stopTheGame(msg):
    user = msg.from_user
    result = game_collection.find_one({'info.user_id' : user.id})
    game_collection.delete_one({'chat_id' : result['chat_id']})


@bot.message_handler(func=lambda msg: msg.chat.type == 'supergroup' and get_current_state(msg.chat.id) == States.T_GAME, commands=['start'])
def start_game_command(msg):

    chat = msg.chat

    
    game = game_collection.find_one({'chat_id' : chat.id})
    players = game['info']

    teams = []
    for player in players:
        teams.append(player)


    teams = np.array_split(teams,2)
    team_one = teams[0]
    team_two = teams[1]

    team_one_str = "1st team :"
    team_two_str = "2nd team : "
    game_collection.update_one(
        {'chat_id' : chat.id},
        {
            '$set' :{ 'current_state' : States.T_START }
        }
    )
    for player in team_one:
        game_collection.update_one(
            {
                'chat_id' : chat.id,
                'info.user_id' : player['user_id']
            }, 
            {
                '$set' : 
                { 
                    'info.$.team_number' : 1 , 
                    'info.$.has_played' : False,
                    'info.$.currently_playing' : False
                }
            }
        )
        team_one_str = team_one_str + " " + player['username']
    for player in team_two:
        game_collection.update_one(
            {
                'chat_id' : chat.id,
                'info.user_id' : player['user_id']
            }, 
            {
                '$set' : 
                { 
                    'info.$.team_number' : 2, 
                    'info.$.has_played' : False ,
                    'info.$.currently_playing' : False
                }
            }
        )
        team_two_str = team_two_str + " " + player['username']

    info = team_one_str + "\n" + team_two_str
    message = bot.send_message(msg.chat.id,info)
    bot.pin_chat_message(chat_id=chat.id,message_id=message.message_id)

    # results = game_collection.find({'chat_id' : chat.id})
    # for result in results :
    #     bot.delete_message(chat_id=chat.id,message_id=result['markup_message_id'])

    keyword_results = words_collection.find()
    keywords = []
    for result in keyword_results :
        keywords.append(result)
    
    random_keyword = random.choice(keywords)
    random_keyword_id = random_keyword['_id']
    
    game_collection.update_one(
            {
                'chat_id' : chat.id, 
            }, { "$set" : 
                {
                    'round' : 0,
                    'round_end_time' : (datetime.now() + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'current_playing_team' : 1, 
                    "team_one_points" : 0,  
                    "team_two_points" : 0,
                    'current_keyword_id' : random_keyword_id 
                }
            }
        )

    cp = assign_new_playee(chat.id)
    send_taboo_message(chat.id,cp)

def get_current_player(chatID):
    cpcol = game_collection.find_one({'chat_id' : chatID})
    current_player = 0
    for info in cpcol['info']:
        if info['currently_playing'] == True :
            current_player = info
    
    return current_player


    
def assign_new_playee(chatID):
    
    
    cpcol = game_collection.find_one({'chat_id' : chatID})
    chatcol_info = cpcol['info']

    for user in chatcol_info:
        game_collection.update_one(
            {
                "chat_id" : chatID,
                "info.user_id" : user['user_id']
            }, { "$set" : {"info.$.currently_playing" : False} }
        )

    current_playing_team_no = cpcol['current_playing_team']
    not_played_users = []
    for np_user in chatcol_info :
        if np_user['isInGame'] == True and np_user['has_played'] == False and np_user['team_number'] == current_playing_team_no:
            not_played_users.append(np_user)

    selected_user = random.choice(not_played_users)
    bot.send_message(chatID,"Cari oyunçu: " + selected_user['username'])
    return selected_user

def send_taboo_message(chatID,selected_user):
    
    cpcol = game_collection.find_one({'chat_id' : chatID})

    res = words_collection.find()
    keywords = []
    for keyword in res :
        keywords.append(keyword)

    new_keyword = random.choice(keywords)
    

    game_collection.update_one(
        {
            'chat_id' : chatID,
        }, {"$set" : { 'current_keyword_id' : new_keyword['_id'] }}
    )

    
    game_collection.update_one(
        {
            'chat_id' : chatID,
            'info.user_id' : selected_user['user_id']
        }, {
            "$set" : 
            {
                'info.$.has_played' : True ,
                'info.$.currently_playing' : True
            }
        }
    )

    not_allowed_words = ""

    for naw in new_keyword['similarTo']:
        not_allowed_words += naw + " "
    
    
    bot.send_message(selected_user['private_chat_id'], 
        "Deməli olduğun : " + new_keyword["word"] + "\n Qadagan sözlər :" + not_allowed_words)        


def set_team_point_and_round(chatID,winning_team_points, points):
    wtp = str(winning_team_points)
    game_collection.update_one(
        {
            'chat_id' : chatID
        },
        {
            '$set' : { 
                wtp : points,
            }
        }
    )

def game_over(chatID):
    current_play = game_collection.find_one({'chat_id' : chatID})
    if current_play['team_one_points'] > current_play['team_two_points']:
        bot.send_message(chatID,"Winner Winner Chicken Dinner : Team 1!")
    elif current_play['team_one_points'] < current_play['team_two_points']:
        bot.send_message(chatID,"Winner Winner Chicken Dinner : Team 2!")
    else:
        bot.send_message(chatID,"Game is draw! No winner :(")
    return True

@bot.message_handler(func=lambda msg: msg.chat.type == 'supergroup' and get_current_state(msg.chat.id) == States.T_START)
def check_for_state(msg):
    
    text = msg.text
    chatID = msg.chat.id
    current_play = game_collection.find_one({'chat_id' : chatID})
    current_playing_team_no = current_play['current_playing_team']
    team_one_points = current_play['team_one_points']   
    team_two_points = current_play['team_two_points']   
    

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    

    round_count = 0
    for data in current_play['info'] :
        if data['team_number'] == 1 :
            round_count = round_count + 1
    
    # check if word is correct
    keyword = words_collection.find_one({'_id' : current_play['current_keyword_id']})
    # answered_user = game_collection.find_one({'chat_id': chatID, 'info.user_id' : msg.from_user.id})
    answered_user = 0
    
    for data in current_play['info']:
        if data['user_id'] == msg.from_user.id:
            answered_user = data
    # check for game over

    if (now) > (current_play['round_end_time']):
        bot.reply_to(msg,"Vaxt bitdi!")
        
        new_time = datetime.strptime(current_play['round_end_time'],'%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
        
        game_collection.update_one(
            {
                'chat_id' : chatID
            },
            {
                "$set" : {
                    'round' : current_play['round'] + 1,
                    'round_end_time': new_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'current_playing_team' : 3 - current_playing_team_no
                }
            }
        )
        if current_play['round'] == (round_count * 2) :
            game_over(chatID)
        else :
            send_taboo_message(chatID,assign_new_playee(chatID))
        return False

    
    logger.info(text)
    logger.info(keyword['word'])
    logger.info(answered_user)

    # check for cheating
    if (text in keyword['similarTo'] or text in keyword['word'] ) and answered_user['currently_playing'] == True:
        if current_playing_team_no == 1 :
            set_team_point_and_round(chatID,"team_two_points",team_two_points + 1)
            bot.reply_to(msg,"Qadağan olunmuş sözdən istifadə : "+ text +" 2ci Team 1 xal qazandı!")
            
        if current_playing_team_no == 2 :
            set_team_point_and_round(chatID,"team_one_points",team_two_points + 1)
            bot.reply_to(msg,"Qadağan olunmuş sözdən istifadə : "+ text +" 1ci Team 1 xal qazandı!")
        send_taboo_message(chatID,get_current_player(chatID))
    elif text in keyword['word'] and answered_user['team_number'] == current_playing_team_no :
        
        if current_playing_team_no == 1 :
            set_team_point_and_round(chatID,"team_one_points",team_one_points + 1)
            bot.reply_to(msg,"1ci Team 1 xal qazandı!")
        
        if current_playing_team_no == 2 :
            set_team_point_and_round(chatID,"team_two_points",team_two_points + 1)
            bot.reply_to(msg,"2ci Team 1 xal qazandi!")
        send_taboo_message(chatID,get_current_player(chatID))

        
    

    



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    userID = call.from_user.id
    username = call.from_user.username
    
    if call.data == 'join':
        bot.answer_callback_query(call.id,url="t.me/{}?start=start".format(botUser.username),cache_time=1)
        user = user_object(call.from_user)
        if user not in players :
            game_collection.update_one(
                {
                    'chat_id' : call.message.chat.id,
                },
                {
                    '$push' : 
                    { 
                        'info' : {
                            'user_id' : userID, 
                            'username' : username,
                            'isInGame' : False
                        }
                    }
                }
            )

    






bot.polling()