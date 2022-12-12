import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
access_tokens = db['access_tokens']
users = db['users']
