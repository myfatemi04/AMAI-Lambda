import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
access_tokens = db['access_tokens']
users = db['users']
interactions = db['interactions']
prompts = db['prompts']
prompt_usage = db['prompt_usage']
retrieval_enhancement_usage = db['retrieval_enhancement_usage']
embeddings_usage = db['embeddings_usage']
text_creations = db['text_creations']

# OLD.
tokens = db['tokens']
