import math
import stripe
from app import app
from extensions import db
from models import Seller, Product
from flask import Blueprint, request, jsonify

stripe.api_key = app.config["STRIPE_SECRET_KEY"]
endpoint_secret = app.config["STRIPE_ENDPOINT_SECRET"]
views = Blueprint("views", __name__, static_folder="static", template_folder="templates")


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    event = None
    payload = request.data
    sig_header = request.headers["STRIPE_SIGNATURE"]

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )

    except ValueError as err:
        # Invalid payload
        raise err

    except stripe.error.SignatureVerificationError as err:
        # Invalid signature
        raise err

    # Handle the event
    if event["type"] == "checkout.session.completed":
        check_out_session = event["data"]["object"]
        print(check_out_session)
        print(check_out_session["payment_intent"])

    elif event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print("payment_intent")
        print(payment_intent)
        split_payment(payment_intent)

    elif event["type"] == "account.updated":
        account = event["data"]["object"]
        seller = Seller.query.filter_by(stripe_account_id=account["id"]).first()
        if not seller.authorized and account["payouts_enabled"]:
            seller.authorized = True
            db.session.commit()

    else:
        print("Unhandled event type {}".format(event["type"]))

    return jsonify(success=True)


def split_payment(payment_intent):
    cart = tuple(payment_intent["metadata"]["cart"].split(","))
    for prod_serial_id in cart:
        prod = Product.query.filter_by(serial_id=prod_serial_id).first()
        transfer = stripe.Transfer.create(
            amount=calc_payout_amount(prod.price, len(cart)),
            currency="cad",
            destination=prod.stripe_account_id,
            transfer_group=payment_intent["transfer_group"],
        )


def calc_payout_amount(original_price, cart_item_count):
    fixed_fee = 30 / cart_item_count  # In Cents
    percentage_fee = 3.6 / 100
    final_fee = percentage_fee * original_price + fixed_fee
    final_payout_amount = original_price - final_fee
    print(math.floor(final_payout_amount))
    return math.floor(final_payout_amount)
