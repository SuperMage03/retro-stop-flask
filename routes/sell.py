import os
import uuid
import stripe
from app import app, db
from models import Seller, Product
from decorators import token_required, verified_seller_required
from flask import Blueprint, request, make_response, jsonify, redirect, send_from_directory

sell = Blueprint("sell", __name__, static_folder="static", template_folder="templates")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]


def add_seller(current_user, stripe_account_id):
    if Seller.query.filter_by(user_id=current_user.id).first() is not None:
        return jsonify({"message": "You are already a seller!"}), 400

    accounts = stripe.Account.list()["data"]
    for account in accounts:
        if account["id"] == stripe_account_id:
            new_seller = Seller(user_id=current_user.id, stripe_account_id=stripe_account_id, authorized=False)
            db.session.add(new_seller)
            db.session.commit()
            return jsonify({"message": "Added Seller!"}), 201

    return jsonify({"message": "No such account ID exist!"}), 400


@sell.route("/create-auth-session", methods=["GET"])
@token_required
def create_auth_session(current_user):
    seller = Seller.query.filter_by(user_id=current_user.id).first()

    if seller is None:
        return make_response(redirect(app.config["CLIENT_URL"]), 400)

    if seller.authorized:
        return make_response(redirect(app.config["CLIENT_URL"]), 400)

    accountLink = stripe.AccountLink.create(
        account=seller.stripe_account_id,
        refresh_url=f"{request.host_url}sell/create-auth-session",
        return_url="https://example.com/success",
        type="account_onboarding"
    )
    return make_response(redirect(accountLink.url), 200)


@sell.route("/onboard-seller", methods=["POST"])
@token_required
def onboard_seller(current_user):
    data = request.json
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if seller is not None:
        if not seller.authorized:
            return make_response(redirect(f"{request.host_url}sell/create-auth-session"), 400)
        else:
            return jsonify({"message": "You are ready to sell!"}), 400

    try:
        account = stripe.Account.create(
            type="express",
            business_type="individual"
        )

        add_seller(current_user, account["id"])

        accountLink = stripe.AccountLink.create(
            account=account["id"],
            refresh_url=f"{request.host_url}sell/create-auth-session",
            return_url="https://example.com/success",
            type="account_onboarding"
        )

        return make_response(redirect(accountLink.url), 200)

    except:
        return make_response(jsonify({"message": "Server Error!"}), 400)


@sell.route("/add-product", methods=["POST"])
@token_required
@verified_seller_required
def add_product(current_user, current_seller):
    data = request.form
    files = request.files

    if data is None:
        return jsonify({"message": "Invalid inputs!"}), 400

    name, description, price = data.get("name"), data.get("description"), data.get("price")
    rom, image = files.get("game"), files.get("image")
    serial_id = uuid.uuid4().hex

    if name is None or description is None or price is None or image is None or rom is None:
        return jsonify({"message": "Invalid inputs!"}), 400

    rom_ext = rom.filename.rsplit('.', 1)[-1].lower()
    image_ext = image.filename.rsplit('.', 1)[-1].lower()
    if rom_ext != "nes":
        return jsonify({"message": "Invalid NES ROM!"}), 400

    if image_ext != "jpg" and image_ext != "jpeg" and image_ext != "png":
        return jsonify({"message": "Invalid Image!"}), 400

    image_name = f"{serial_id}.{image_ext}"
    rom_name = f"{serial_id}.{rom_ext}"

    try:
        image.save(os.path.join(app.root_path, "static", "rom_images", image_name))
        rom.save(os.path.join(app.root_path, "protected", "rom_files", rom_name))

    except:
        return jsonify({"message": "Failed to upload files!"}), 500

    stripe_product, stripe_price = None, None
    try:
        stripe_product = stripe.Product.create(
            name=name,
            description=description,
            images=[f"{request.host_url}rom_images/{image_name}"]
        )

        stripe_price = stripe.Price.create(
            currency="cad",
            product=stripe_product.id,
            unit_amount=int(float(price) * 100)
        )

    except:
        if stripe_product is not None:
            stripe.Product.delete(stripe_product.id)
        return jsonify({"message": "Error when using Stripe API!"}), 500

    try:
        new_prod = Product(
            user_id=current_user.id,
            serial_id=serial_id,
            stripe_account_id=current_seller.stripe_account_id,
            stripe_product_id=stripe_product.id,
            stripe_price_id=stripe_price.id,
            name=name,
            description=description,
            price=int(float(price) * 100),
            rom_name=rom_name,
            image_name=image_name
        )

        db.session.add(new_prod)
        db.session.commit()

    except:
        return jsonify({"message": "Failed to save to Database!"}), 500

    return jsonify({"message": "Success!"}), 201
