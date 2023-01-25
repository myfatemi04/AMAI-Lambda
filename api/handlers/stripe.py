from api.decorator import lambda_api
import api.stripe_utils

@lambda_api('stripe', environment_variables=['STRIPE_API_KEY'], require_auth=True)
def stripe(body, user):
    request_type = body.pop("request_type")

    if request_type == "get_usage":
        return get_stripe_usage(body, user)
    elif request_type == "subscribe":
        return create_subscription(body, user)
    elif request_type == "unsubscribe":
        return cancel_subscription(body, user)
    elif request_type == "get_subscription":
        return get_subscription(body, user)

    return (400, {"error": "invalid request_type"})

def get_subscription(body, user):
    email = user['email']
    name = user['name']

    subscription = api.stripe_utils.get_augmate_subscription(api.stripe_utils.obtain_stripe_customer(email, name))

    return (200, {"subscription": subscription})

def create_subscription(body, user):
    email = user['email']
    name = user['name']

    subscription = api.stripe_utils.create_augmate_subscription_if_not_existing(api.stripe_utils.obtain_stripe_customer(email, name))

    return (200, {"subscription": subscription})

def cancel_subscription(body, user):
    email = user['email']
    name = user['name']

    subscription = api.stripe_utils.cancel_augmate_subscription(api.stripe_utils.obtain_stripe_customer(email, name))

    return (200, {"subscription": subscription})

def get_stripe_usage(body, user):
    email = user['email']
    name = user['name']

    usage = api.stripe_utils.get_usage(email, name)
    
    return (200, {"usage": {"text_generation": usage}})
