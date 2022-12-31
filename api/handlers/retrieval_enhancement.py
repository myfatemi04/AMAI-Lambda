import hashlib
import io
import os

import api.errors
import ftfy
import requests
from api.db import retrieval_enhancement_usage
from api.decorator import lambda_api
from api.pdftotext import pdftext_from_fileobj
from api.savetos3 import save_to_s3


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
	response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"})
	response.raise_for_status()

	# check if it's a PDF
	if response.headers["content-type"].startswith("application/pdf"):
		print("PDF!")
		type = "text-from-pdf"
		content = pdftext_from_fileobj(io.BytesIO(response.content))
		# print(content)
		print("Got result.")
	else:
		print(response.headers['content-type'])
		type = "html"
		content = response.text

	content = ftfy.fix_text(content)

	return {"type": type, "content": content}

@lambda_api("retrieval_enhancement", ["BING_SEARCH_V7_SUBSCRIPTION_KEY1", "MONGO_URI"], require_auth=True)
def retrieval_enhancement(body, user):
	query: str = body.get("query")
	backend = body.get("backend")

	if query is None or backend is None:
		return api.errors.missing_from_request("missing query or backend")

	result_content = None
	if backend == "bing":
		result_content = _bing(query)
		result_type = "search_results"
	elif backend == "proxy":
		try:
			result = _proxy(query)
			result_content = result['content']
			result_type = result['type']
			filename = 'proxy/' + result_type + "_" + hashlib.sha256(query.encode('utf-8')).hexdigest()
			# save result in s3
			save_to_s3('augmate-retrieval-content', filename, result_content)
			
			result_type = 's3'
			result_content = filename
		except Exception as e:
			return api.errors.unsuccessful_retrieval(str(e))
	else:
		return api.errors.not_found("backend")

	retrieval_enhancement_usage.insert_one({
		"user_id": user["_id"],
		"query": query,
		"backend": backend,
		"result": {
			"content": result_content,
			"type": result_type
		},
	})

	return 200, {"result": {"content": result_content, "type": result_type}}

# if __name__ == '__main__':
# 	query = "https://arxiv.org/pdf/2008.11976.pdf"
# 	try:
# 		result = _proxy(query)
# 		result_content = result['content']
# 		result_type = result['type']
# 		filename = 'proxy/' + result_type + "_" + hashlib.sha256(query.encode('utf-8')).hexdigest()
# 		# save result in s3
# 		save_to_s3('augmate-retrieval-content', filename, result_content)
		
# 		result_type = 's3'
# 		result_content = filename
# 	except Exception as e:
# 		print(e)
