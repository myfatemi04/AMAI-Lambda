import os

import api.errors
import requests
from api.db import retrieval_enhancement_usage
from api.decorator import lambda_api


def _bing(query):
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

def _proxy(url):
	try:
		response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"})
		response.raise_for_status()
		return response.text
	except Exception as ex:
		raise ex

@lambda_api("retrieval_enhancement", ["BING_SEARCH_V7_SUBSCRIPTION_KEY1", "MONGO_URI"], require_auth=True)
def retrieval_enhancement(body, user):
	query = body.get("query")
	backend = body.get("backend")

	if query is None or backend is None:
		return api.errors.missing_from_request("missing query or backend")

	result = None
	if backend == "bing":
		result = _bing(query)
	elif backend == "proxy":
		result = _proxy(query)
	else:
		return api.errors.not_found("backend")

	retrieval_enhancement_usage.insert_one({
		"user_id": user["_id"],
		"query": query,
		"backend": backend,
		"result": result,
	})

	return 200, {"result": result}
