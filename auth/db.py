import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
oauth_tokens = db['oauth_tokens']
users = db['users']
