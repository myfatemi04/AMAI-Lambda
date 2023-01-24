import time
from api.decorator import lambda_api
import api.db
import api.prompts
import api.errors
import api.stripe_utils

@lambda_api("generate_for_prompt", ["MONGO_URI", "STRIPE_API_KEY"], require_auth=True)
def generate_for_prompt(body, user):
    prompt_id = body.get("prompt_id")
    variables = body.get("variables")

    if prompt_id is None or variables is None:
        return api.errors.missing_from_request("missing prompt_id, token, or variables")

    prompt = api.prompts.get_prompt(prompt_id)
    if prompt is None:
        return api.errors.not_found("prompt_id")

    if type(variables) is not dict:
        return api.errors.missing_from_request("variables must be dict")

    user_id = user['_id']

    try:
        completion = prompt(**variables)
    except api.prompts.MissingVariableException as e:
        return api.errors.missing_from_request(f"variable {e.variable}")

    # add completion tokens to text generation usage
    api.stripe_utils.add_usage(user['email'], user['name'], completion['completion_tokens'])

    api.db.prompt_usage.insert_one({
        "user_id": user_id,
        "prompt_id": prompt_id,
        "prompt_template": prompt.template,
        "prompt_type": prompt.__class__.__name__,
        "variables": variables,
        "completion": completion['text'],
        "completion_prompt_tokens": completion['prompt_tokens'],
        "completion_completion_tokens": completion['completion_tokens'],
        "backend": "openai:" + prompt.model_key,
        "timestamp": time.time(),
    })

    if not completion:
        print(f"WARNING: No completion; {prompt_id=} {variables=}")

    return (200, {"completion": completion['text'], "prompt_tokens": completion['prompt_tokens'], "completion_tokens": completion['completion_tokens']})
