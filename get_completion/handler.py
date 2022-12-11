import json
from apis import get_api
from db import tokens
import prompts

def r(code, body):
	print("Response {} with body {}".format(code, json.dumps(body)))
	return {
		'statusCode': code,
		'body': json.dumps(body),
		'headers': {
			'Access-Control-Allow-Origin': '*',
		}
	}

def lambda_general_completion(event, context):
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

		model = get_api(method)
		if model is None:
			return r(404, {"error": "Invalid method", "completion": "[invalid method]"})

		completion = model(prompt, temperature=temperature, max_tokens=max_tokens, stop=stop)

		if not completion:
			print(f"WARNING: No completion; {prompt=} {model=} {max_tokens=}")

		return r(200, {"completion": completion})
		
	except Exception as e:
		import traceback
		return r(500, {"error": "Internal Server Error: " + traceback.format_exc(), "completion": "[internal server error]"})

def lambda_prompt_completion(event, context):
	try:
		body = json.loads(event.get("body"))
		prompt_id = body.get("prompt_id")
		variables = body.get("variables")
		token = body.get("token")

		print("Received event with body:", event.get('body'))

		if prompt_id is None or token is None or variables is None:
			return r(400, {"error": "Invalid request: Missing 'prompt_id' or 'token' parameter or 'variables' parameter"})

		prompt = prompts.get_prompt(prompt_id)
		if prompt is None:
			return r(404, {"error": "Invalid `prompt_id`: not found", "completion": "[invalid prompt_id]"})

		if type(variables) is not dict:
			return r(400, {"error": "Invalid `variables`: must be dict", "completion": "[invalid variables]"})

		token_data = tokens.find_one({"token": token})
		if token_data is None:
			return r(401, {"error": "Invalid token", "completion": "[invalid token]"})

		completion = prompt(**variables)

		if not completion:
			print(f"WARNING: No completion; {prompt_id=} {variables=} {token=}")

		return r(200, {"completion": completion})
		
	except Exception as e:
		import traceback
		return r(500, {"error": "Internal Server Error: " + traceback.format_exc(), "completion": "[internal server error]"})

