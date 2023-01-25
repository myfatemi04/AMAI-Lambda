import os
import time
import traceback

import api.db
import api.errors
import api.stripe_utils
import stripe
import stripe.error
from api.decorator import lambda_api

# Webhooks intro:
# https://stripe.com/docs/webhooks

# Events overview:
# https://stripe.com/docs/api/events/types

@lambda_api('stripe_webhook', environment_variables=['STRIPE_API_KEY', 'STRIPE_WEBHOOK_SECRET', 'MONGO_URI'], require_auth=False, use_raw=True)
def stripe_webhook(request):
    payload = request['body']
    sig_header = request['headers']['stripe-signature']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ['STRIPE_WEBHOOK_SECRET']
        )
        api.db.stripe_events.insert_one({"object": event.data.object.to_dict_recursive(), "type": event.type, "timestamp": time.time()})

        if event.type == 'customer.subscription.updated':
            api.stripe_utils.handle_subscription_updated(event.data.object)
        elif event.type == 'customer.subscription.deleted':
            api.stripe_utils.handle_subscription_deleted(event.data.object)
        else:
            print("Unhandled event type: {}".format(event.type))

    except ValueError:
        traceback.print_exc()
        return (400, {"error": "invalid payload"})

    except stripe.error.SignatureVerificationError:
        traceback.print_exc()
        return (400, {"error": "invalid signature"})

    return (200, {"success": True})
