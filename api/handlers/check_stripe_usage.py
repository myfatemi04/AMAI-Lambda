from api.decorator import lambda_api
import api.stripe_utils

@lambda_api('check_stripe_usage', environment_variables=['STRIPE_API_KEY'], require_auth=True)
def check_stripe_usage(body, user):
    email = user['email']
    name = user['name']

    usage = api.stripe_utils.get_usage(email, name)
    
    return (200, {"usage": {"text_generation": usage}})
