import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
tokens = db['tokens']