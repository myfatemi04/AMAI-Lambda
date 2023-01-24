from api.decorator import lambda_api
import api.errors
import api.stripe_utils
import stripe
import stripe.error
import os

@lambda_api('stripe_webhook', environment_variables=['STRIPE_API_KEY'], require_auth=False, use_raw=True)
def stripe_webhook(request):
    payload = request['body']
    sig_header = request['headers']['STRIPE_SIGNATURE']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ['STRIPE_API_KEY']
        )
        print("EVENT")
        print(event)
    except ValueError as e:
        return (400, {"error": "invalid payload"})
    except stripe.error.SignatureVerificationError as e:
        return (400, {"error": "invalid signature"})

    return (200, {"success": True})
