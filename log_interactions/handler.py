import json
import os
import pymongo
from bson.objectid import ObjectId

def r(code, body):
	return {
		'statusCode': code,
		'body': json.dumps(body),
		'headers': {
			'Access-Control-Allow-Origin': '*',
		}
	}

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
interactions = db['interactions']
tokens = db['tokens']

def find_token(token: str):
	return tokens.find_one({"token": token})

def get_interaction(interaction_id: str):
	return interactions.find_one({"_id": ObjectId(interaction_id)})

def create_interaction(token, prompt):
	result = interactions.insert_one({
		"prompt": prompt,
		"token": token,
		"events": [],
	})
	return str(result.inserted_id)

def log_copy(interaction_id: str, completion: str):
		interactions.update_one({
				"_id": ObjectId(interaction_id)},
				{"$push": {
						"events": {
								"completion": completion,
								"type": "copy"
						}
				}
		})

def log_feedback(interaction_id: str, completion: str, feedback: str):
		interactions.update_one({
				"_id": ObjectId(interaction_id)},
				{"$push": {
						"events": {
								"completion": completion,
								"feedback": feedback,
								"type": "feedback"
						}
				}
		})

def log_continuation(interaction_id: str, completion: str):
		interactions.update_one({
				"_id": ObjectId(interaction_id)},
				{"$push": {
						"events": {
								"completion": completion,
								"type": "continuation"
						}
				}
		})

def sel(body, keys):
	return [body.get(key) for key in keys]

def lambda_handler(event, context):
	try:
		body = json.loads(event.get("body"))
		token = body.get("token")

		if token is None:
			return r(400, {"error": "Invalid request: `token` not provided"})
		
		if find_token(token) is None:
			return r(401, {"error": "Invalid token"})

		t = body.get('type')
		if t == 'create_interaction':
			prompt = body.get('prompt')
			if prompt is None:
				return r(400, {"error": "Invalid request: `prompt` not provided"})
			return r(200, {"interaction_id": create_interaction(token, prompt)})
		elif t == 'log_copy':
			interaction_id, completion = sel(body, ['interaction_id', 'completion'])
			if interaction_id is None or completion is None:
				return r(400, {"error": "Invalid request: `interaction_id` or `completion` not provided"})

			if get_interaction(interaction_id) is None:
				return r(404, {"error": "Invalid interaction_id"})

			log_copy(interaction_id, completion)
			return r(200, {})
		elif t == 'log_feedback':
			interaction_id, completion, feedback = sel(body, ['interaction_id', 'completion', 'feedback'])
			if interaction_id is None or completion is None or feedback is None:
				return r(400, {"error": "Invalid request: `interaction_id`, `completion`, or `feedback` not provided"})

			if get_interaction(interaction_id) is None:
				return r(404, {"error": "Invalid interaction_id"})

			log_feedback(interaction_id, completion, feedback)
			return r(200, {})
		elif t == 'log_continuation':
			interaction_id, completion = sel(body, ['interaction_id', 'completion'])
			if interaction_id is None or completion is None:
				return r(400, {"error": "Invalid request: `interaction_id` or `completion` not provided"})

			if get_interaction(interaction_id) is None:
				return r(404, {"error": "Invalid interaction_id"})

			log_continuation(interaction_id, completion)
			return r(200, {})
		else:
			return r(400, {"error": "Invalid request: `type` not provided or invalid"})

	except Exception as e:
		import traceback
		return r(500, {"error": "Internal Server Error: " + traceback.format_exc(), "completion": "[internal server error]"})
