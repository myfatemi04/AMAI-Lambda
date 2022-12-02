import functools
import json
import os
import requests

def huggingface(model_key, prompt: str, temperature=0.7, max_tokens=120):
	API_URL = "https://api-inference.huggingface.co/models/" + model_key # "bigscience/bloom"
	response = requests.post(API_URL, headers={
		"Authorization": "Bearer " + os.environ['HUGGINGFACE_API_KEY'],
	}, json={
		"inputs": prompt,
		"parameters": {
			"max_length": max_tokens,
			"temperature": temperature,
			"return_full_text": False,
		}
	})
	return response.json()[0]['generated_text']

def gpt3(prompt: str, temperature=0.7, max_tokens=120) -> str:
	response = requests.post('https://api.openai.com/v1/completions', json={
		'model': 'text-davinci-003',
		'prompt': prompt,
		'temperature': temperature,
		'max_tokens': max_tokens,
		'top_p': 1,
		'frequency_penalty': 0,
		'presence_penalty': 0,
	}, headers={
		'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
		'Content-Type': 'application/json',
	})
	response = response.json()

	return response['choices'][0]['text']

models = {
	'gpt3': gpt3,
	'gptj': functools.partial(huggingface, 'EleutherAI/gpt-j-6B'),
}

def r(code, body):
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

		if prompt is None or token is None:
			return r(400, {"error": "Invalid request: Missing 'prompt' or 'token' parameter"})

		max_tokens = 120
		method = 'gpt3'

		if token == '$demo':
			max_tokens = 25
		elif token == '$dev:gptj':
			method = 'gptj'
		elif token not in os.environ['TOKENS'].split('|'):
			return r(403, {"error": "Invalid token", "completion": "[invalid token]"})
			
		completion = models[method](prompt, temperature=0.7, max_tokens=max_tokens)

		return r(200, {"completion": completion})
		
	except Exception as e:
		import traceback
		return r(500, {"error": "Internal Server Error: " + traceback.format_exc(), "completion": "[internal server error]"})
