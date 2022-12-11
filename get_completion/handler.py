import functools
import json
import os
import requests
import pymongo

def huggingface(model_key, prompt: str, temperature=0.7, max_tokens=120, stop=None):
	API_URL = "https://api-inference.huggingface.co/models/" + model_key # "bigscience/bloom"
	response = requests.post(API_URL, headers={
		"Authorization": "Bearer " + os.environ['HUGGINGFACE_API_KEY'],
	}, json={
		"inputs": prompt,
		"parameters": {
			"max_length": max_tokens,
			"temperature": temperature,
			"return_full_text": False,
			"stop": stop,
		}
	})
	j = response.json()
	if type(j) is list:
		j = j[0]
	return j['generated_text']

def openai(model_key, prompt: str, temperature=0.7, max_tokens=120, stop=None) -> str:
	body = {
		'model': model_key,
		'prompt': prompt,
		'temperature': temperature,
		'max_tokens': max_tokens,
		'top_p': 1,
		'frequency_penalty': 0,
		'presence_penalty': 0,
		'stop': stop,
	}
	headers = {
		'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
		'Content-Type': 'application/json',
	}
	response = requests.post('https://api.openai.com/v1/completions', json=body, headers=headers)
	response = response.json()

	print("POST https://api.openai.com/v1/completions")
	print(f"{body=} {headers=}")
	print(f"{response=}")

	if 'choices' not in response:
		raise ValueError("Invalid response from OpenAI: " + str(response))

	return response['choices'][0]['text']

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
interactions = db['interactions']
tokens = db['tokens']

def r(code, body):
	print("Response {} with body {}".format(code, json.dumps(body)))
	return {
		'statusCode': code,
		'body': json.dumps(body),
		'headers': {
			'Access-Control-Allow-Origin': '*',
		}
	}

def lambda_handler(event, context):
	try:
		body = json.loads(event.get("body"))
		prompt = body.get("prompt")
		token = body.get("token")

		print("Received event with body:", event.get('body'))

		if prompt is None or token is None:
			return r(400, {"error": "Invalid request: Missing 'prompt' or 'token' parameter"})

		max_tokens = 120

		token_data = tokens.find_one({"token": token})
		if token_data is None:
			return r(401, {"error": "Invalid token", "completion": "[invalid token]"})

		max_tokens: int = token_data.get('max_tokens', 120)
		method: str = token_data.get('method', 'openai:text-davinci-003')

		temperature = token_data.get('temperature', 0.7)
		stop = token_data.get('stop', None)

		if method.startswith("hf:"):
			model = functools.partial(huggingface, method[3:])
		elif method.startswith("openai:"):
			model = functools.partial(openai, method[7:])

		completion = model(prompt, temperature=temperature, max_tokens=max_tokens, stop=stop)

		if not completion:
			print(f"WARNING: No completion; {prompt=} {model=} {max_tokens=}")

		return r(200, {"completion": completion})
		
	except Exception as e:
		import traceback
		return r(500, {"error": "Internal Server Error: " + traceback.format_exc(), "completion": "[internal server error]"})
