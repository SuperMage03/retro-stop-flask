import jwt
import bcrypt
import datetime
from models import User
from extensions import db
from copy import deepcopy
from decorators import token_required
from flask import Blueprint, request, make_response, jsonify, redirect

auth = Blueprint("auth", __name__, static_folder="static", template_folder="templates")
auth.config = {}


@auth.record
def record_params(setup_state):
    app = setup_state.app
    auth.config = deepcopy(app.config)


@auth.route("/all", methods=["GET"])
def get_all():
    users = User.query.all()

    output = []
    for user in users:
        dic = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password": user.password.decode("utf-8"),
            "games": user.get_games()
        }
        output.append(dic)

    return jsonify({"users": output})


@auth.route("/login", methods=["POST"])
def login():
    token = request.cookies.get("token")
    if token is not None:
        try:
            jwt.decode(token, auth.config["SECRET_KEY"], algorithms=["HS256"])
            return jsonify({"message": "Logged in already!"}), 400
        except:
            pass

    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if user is None:
        return jsonify({"message": "User Doesn't Exist!"}), 404

    if not bcrypt.checkpw(data["password"].encode("utf8"), user.password):
        return jsonify({"message": "Password Doesn't Match!"}), 403

    token_expire_time = 60 * 60 * 24
    token_expire_data = datetime.datetime.utcnow() + datetime.timedelta(seconds=token_expire_time)
    token = jwt.encode({"user_email": user.email, "exp": token_expire_data}, auth.config["SECRET_KEY"],
                       algorithm="HS256")

    res = make_response(jsonify({"message": "Logged In", "token": token}), 200)
    res.set_cookie("token", token, max_age=token_expire_time)

    return res


@auth.route("/register", methods=["POST"])
def register():
    data = request.json

    if User.query.filter_by(email=data["email"]).first() is not None:
        return jsonify({"message": "This E-Mail is already registered!"}), 403

    hashed_password = bcrypt.hashpw(data["password"].encode("utf8"), bcrypt.gensalt(10))
    new_user = User(name=data["name"], email=data["email"], password=hashed_password, games="")
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "New User Created!"})


@auth.route("/logout", methods=["GET"])
@token_required
def logout(current_user):
    res = make_response(redirect("/home"), 200)
    res.set_cookie("token", "", max_age=1)
    return res
