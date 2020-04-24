

from pymongo import MongoClient


client = MongoClient("mongodb+srv://taboobot:kNdsLYJvr9dSQ6JH@cluster0-ufme0.mongodb.net/test?retryWrites=true&w=majority")


database = client.test


game_collection = database["games"]
markup_message_collection = database['markup_message_collection']
