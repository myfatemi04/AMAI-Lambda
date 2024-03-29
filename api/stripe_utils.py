import time
import stripe
import os

stripe.api_key = os.environ['STRIPE_API_KEY']

# text_generation_product_id = os.environ['TEXT_GENERATION_PRODUCT_ID']
text_generation_product_id = 'prod_N9SiGTLwdAk8NS'

def obtain_stripe_customer(email: str, name: str):
    customers = stripe.Customer.list(email=email)
    if len(customers) == 0:
        customer = stripe.Customer.create(email=email, name=name)
        return customer
    else:
        return customers.data[0]

def create_augmate_subscription_if_not_existing(customer: stripe.Customer):
    current_subscription = get_augmate_subscription(customer)

    if not current_subscription:
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {"price": get_price(text_generation_product_id).id}
            ]
        )

    return subscription

def cancel_augmate_subscription(customer: stripe.Customer):
    subscription = get_augmate_subscription(customer)
    if subscription is None:
        return None

    subscription = stripe.Subscription.modify(
        subscription.id,
        cancel_at_period_end=True,
    )

    return subscription

def get_augmate_subscription(customer: stripe.Customer):
    subscriptions = stripe.Subscription.list(customer=customer.id)

    if len(subscriptions) == 0:
        return None
    
    return subscriptions.data[0]

def get_price(product_id: str):
    prices = stripe.Price.list(product=product_id, active=True)
    return prices.data[0]

def obtain_subscription_item(subscription: stripe.Subscription, product_id: str):
    subscription_items = stripe.SubscriptionItem.list(subscription=subscription.id)

    for item in subscription_items.data:
        if item.plan.product == product_id:
            return item
    else:
        item = stripe.SubscriptionItem.create(
            subscription=subscription.id,
            price=get_price(product_id).id,
        )
        return item

def add_usage_record_to_subscription_item(subscription_item: stripe.SubscriptionItem, word_count: int) -> stripe.UsageRecord:
    usage_record = stripe.UsageRecord.create(
        subscription_item=subscription_item.stripe_id,
        quantity=word_count,
        timestamp=int(time.time()),
    )
    return usage_record

def add_usage(email: str, name: str, token_count: int):
    customer = obtain_stripe_customer(email, name)
    subscription = get_augmate_subscription(customer)
    subscription_item = obtain_subscription_item(subscription, text_generation_product_id)
    usage_record = add_usage_record_to_subscription_item(subscription_item, token_count)
    return usage_record

def get_usage(email: str, name: str):
    customer = obtain_stripe_customer(email, name)
    subscription = get_augmate_subscription(customer)
    subscription_item = obtain_subscription_item(subscription, text_generation_product_id)
    summaries = stripe.SubscriptionItem.list_usage_record_summaries(subscription_item.id)
    most_recent_summary = summaries.data[0]
    return most_recent_summary.total_usage

# Customer events:
# https://stripe.com/docs/api/events/types
# Subscription events:
# https://stripe.com/docs/api/subscriptions/object

def handle_subscription_updated(subscription: stripe.Subscription):
    import api.db

    customer_id = subscription['customer']
    customer_email = stripe.Customer.retrieve(customer_id).email

    api.db.users.update_one({"email": customer_email}, {"$set": {"subscription": subscription}})

def handle_subscription_deleted(subscription: stripe.Subscription):
    import api.db

    customer_id = subscription['customer']
    customer_email = stripe.Customer.retrieve(customer_id).email

    api.db.users.update_one({"email": customer_email}, {"$set": {"subscription": None}})
