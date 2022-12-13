from api.decorator import lambda_api
import api.db
import api.prompts
import api.errors

@lambda_api("generate_for_prompt", ["MONGO_URI"], require_auth=True)
def generate_for_prompt(body, user):
    prompt_id = body.get("prompt_id")
    variables = body.get("variables")

    if prompt_id is None or variables is None:
        return api.errors.bad_request("missing prompt_id, token, or variables")

    prompt = api.prompts.get_prompt(prompt_id)
    if prompt is None:
        return api.errors.not_found("prompt_id")

    if type(variables) is not dict:
        return api.errors.bad_request("variables must be dict")

    user_id = user['_id']
    completion = prompt(**variables)

    api.db.prompt_usage.insert_one({
        "user_id": user_id,
        "prompt_id": prompt_id,
        "prompt_template": prompt.template,
        "prompt_type": prompt.__class__.__name__,
        "variables": variables,
        "completion": completion,
    })

    if not completion:
        print(f"WARNING: No completion; {prompt_id=} {variables=}")

    return (200, {"completion": completion})
