

from pymongo import MongoClient
import json



client = MongoClient("mongodb+srv://taboobot:kNdsLYJvr9dSQ6JH@taboobotcluster-ufme0.mongodb.net/test?retryWrites=true&w=majority")
database = client.test


game_collection = database["games"]
markup_message_collection = database['markup_message_collection']
current_plays_collection = database['current_plays']

words_collection = database['words']

with open('words.json') as json_file:
    data = json.load(json_file)
    words_collection.insert_many(data)

