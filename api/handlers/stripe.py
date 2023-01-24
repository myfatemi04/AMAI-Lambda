from api.decorator import lambda_api
import api.stripe_utils

@lambda_api('stripe', environment_variables=['STRIPE_API_KEY'], require_auth=True)
def stripe(body, user):
    request_type = body.pop("request_type")

    if request_type == "get_usage":
        return get_stripe_usage(body, user)

    return (400, {"error": "invalid request_type"})

def get_stripe_usage(body, user):
    email = user['email']
    name = user['name']

    usage = api.stripe_utils.get_usage(email, name)
    
    return (200, {"usage": {"text_generation": usage}})
