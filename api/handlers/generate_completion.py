from api.decorator import lambda_api
from api.llms import get_api
from api.db import tokens

@lambda_api("generate_completion", ["MONGO_URI"], require_auth=False)
def generate_completion(body):
    prompt = body.get("prompt")
    token = body.get("token")

    if prompt is None or token is None:
        return (400, {"error": "Invalid request: Missing 'prompt' or 'token' parameter"})

    token_data = tokens.find_one({"token": token})
    if token_data is None:
        return (401, {"error": "Invalid token", "completion": "[invalid token]"})

    max_tokens: int = token_data.get('max_tokens', 120)
    method: str = token_data.get('method', 'openai:text-davinci-003')

    temperature = token_data.get('temperature', 0.7)
    stop = token_data.get('stop', None)

    model = get_api(method)
    if model is None:
        return (404, {"error": "Invalid method", "completion": "[invalid method]"})

    completion = model(prompt, temperature=temperature, max_tokens=max_tokens, stop=stop)

    if not completion:
        print(f"WARNING: No completion; {prompt=} {model=} {max_tokens=}")

    return (200, {"completion": completion})
