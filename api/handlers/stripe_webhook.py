from api.decorator import lambda_api
import api.errors
import api.stripe_utils
import stripe
import stripe.error
import os
import traceback

@lambda_api('stripe_webhook', environment_variables=['STRIPE_API_KEY', 'STRIPE_WEBHOOK_SECRET'], require_auth=False, use_raw=True)
def stripe_webhook(request):
    # print(request)
    payload = request['body']
    sig_header = request['headers']['stripe-signature']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ['STRIPE_WEBHOOK_SECRET']
        )
        print("EVENT")
        print(event)
    except ValueError as e:
        traceback.print_exc()
        return (400, {"error": "invalid payload"})
    except stripe.error.SignatureVerificationError as e:
        traceback.print_exc()
        return (400, {"error": "invalid signature"})

    return (200, {"success": True})
