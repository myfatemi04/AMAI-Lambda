import requests
import os
import json
from db import tokens

def r(code, body):
	print("Response {} with body {}".format(code, json.dumps(body)))
	return {
		'statusCode': code,
		'body': json.dumps(body),
		'headers': {
			'Access-Control-Allow-Origin': '*',
		}
	}

def bing(query):
	# Add your Bing Search V7 subscription key and endpoint to your environment variables.
	subscription_key = os.environ['BING_SEARCH_V7_SUBSCRIPTION_KEY1']
	endpoint = "https://api.bing.microsoft.com/v7.0/search"

	params = {'q': query, 'mkt': 'global'}
	headers = {'Ocp-Apim-Subscription-Key': subscription_key}

	try:
		response = requests.get(endpoint, headers=headers, params=params)
		response.raise_for_status()
		body = response.json()

		return {
			"pages": [{
				"title": result["name"],
				"url": result["url"],
				"snippet": result["snippet"]
			} for result in body["webPages"]["value"]],

			"related_searches": [
				result["text"] for result in (body["relatedSearches"]["value"] if 'relatedSearches' in body else [])
			],
		}
	except Exception as ex:
		raise ex

def proxy(url):
	try:
		response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"})
		response.raise_for_status()
		return response.text
	except Exception as ex:
		raise ex

def lambda_handler(event, body):
	try:
		body = json.loads(event.get("body"))
		token = body.get("token")
		query = body.get("query")
		backend = body.get("backend")

		if token is None or query is None or backend is None:
			return r(400, {"error": "Invalid request: `token` or `query` or `backend` not provided"})
		
		token_data = tokens.find_one({"token": token})
		if token_data is None:
			return r(401, {"error": "Invalid token"})

		if backend == "bing":
			return r(200, {"result": bing(query)})
		elif backend == "proxy":
			return r(200, {"result": proxy(query)})
		else:
			return r(404, {"error": "Backend not found"})
			
	except Exception as e:
		import traceback
		traceback.print_exc()
		return r(400, {"error": "Invalid request: " + str(e)})
