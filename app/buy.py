import uuid
import stripe
from models import Product
from decorators import token_required
from flask import Blueprint, request, make_response, jsonify, redirect, send_from_directory

buy = Blueprint("buy", __name__, static_folder="static", template_folder="templates")


@buy.route("/check-out", methods=["POST"])
@token_required
def check_out(current_user):
    data = request.json
    cart = data["cart"]

    total_price = 0
    line_items = []
    for prod_serial_id in cart:
        prod = Product.query.filter_by(serial_id=prod_serial_id).first()
        if prod is None:
            return jsonify({"message": "No product exist! Might be server error!"}), 500

        total_price += prod.price
        line_items.append({"price": prod.stripe_price_id, "quantity": 1})

    transfer_group_id = uuid.uuid4().hex
    session = stripe.checkout.Session.create(
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        payment_method_types=["card"],
        line_items=line_items,
        payment_intent_data={
            "transfer_group": transfer_group_id,
            "metadata": {
                "cart": ",".join(cart)
            }
        },
        mode="payment",
        metadata={
            "cart": ",".join(cart),
            "buyer_id": current_user.id
        }
    )

    print(session)
    return make_response(redirect(session.url), 200)
