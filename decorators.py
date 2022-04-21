import jwt
from app import app
from models import User, Seller
from functools import wraps
from flask import request, jsonify


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if token is None:
            return jsonify({"message": "Access Denied!"}), 401

        try:
            decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            user_email = decoded_token["user_email"]
            current_user = User.query.filter_by(email=user_email).first()
            return f(current_user, *args, **kwargs)
        except:
            return jsonify({"message": "Invalid Token"}), 401

    return decorated


def verified_seller_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        current_seller = Seller.query.filter_by(user_id=current_user.id).first()
        if current_seller is None:
            return jsonify({"message": "Didn't apply for seller!"}), 401

        if not current_seller.authorized:
            return jsonify({"message": "Didn't finish filling the seller information!"}), 400

        return f(current_user, current_seller, *args, **kwargs)

    return decorated
