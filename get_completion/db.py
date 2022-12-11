import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
interactions = db['interactions']
tokens = db['tokens']
prompts = db['prompts']
