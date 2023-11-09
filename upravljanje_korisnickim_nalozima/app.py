from flask import Flask
from flask import request, Response
from flask import jsonify

from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import get_jwt

from configuration import Configuration

from models import database
from models import User

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
jwt = JWTManager(application)

import re


@application.route("/register_customer", methods=["POST"])
def register_customer():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if forenameEmpty:
        return {"message": "Field forename is missing."}, 400
    if surnameEmpty:
        return {"message": "Field surname is missing."}, 400
    if emailEmpty:
        return {"message": "Field email is missing."}, 400
    if passwordEmpty:
        return {"message": "Field password is missing."}, 400

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"

    if not re.match(pattern, email):
        return {"message": "Invalid email."}, 400

    if len(password) < 8:
        return {"message": "Invalid password."}, 400

    if User.query.filter(User.email == email).all():
        return {"message": "Email already exists."}, 400

    user = User(
        forename=forename,
        surname=surname,
        email=email,
        password=password,
        role="customer",
    )
    database.session.add(user)
    database.session.commit()

    return Response(status=200)


@application.route("/register_courier", methods=["POST"])
def register_courier():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if forenameEmpty:
        return {"message": "Field forename is missing."}, 400
    if surnameEmpty:
        return {"message": "Field surname is missing."}, 400
    if emailEmpty:
        return {"message": "Field email is missing."}, 400
    if passwordEmpty:
        return {"message": "Field password is missing."}, 400

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"

    if not re.match(pattern, email):
        return {"message": "Invalid email."}, 400

    if len(password) < 8:
        return {"message": "Invalid password."}, 400

    if User.query.filter(User.email == email).all():
        return {"message": "Email already exists."}, 400

    user = User(
        forename=forename,
        surname=surname,
        email=email,
        password=password,
        role="courier",
    )
    database.session.add(user)
    database.session.commit()

    return Response(status=200)


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if emailEmpty:
        return {"message": "Field email is missing."}, 400
    if passwordEmpty:
        return {"message": "Field password is missing."}, 400

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"

    if not re.match(pattern, email):
        return {"message": "Invalid email."}, 400

    user = User.query.filter(User.email == email, User.password == password).first()

    if not user:
        return {"message": "Invalid credentials."}, 400

    access_token = create_access_token(identity=user.email)
    claims = {"forename": user.forename, "surname": user.surname, "role": user.role}

    access_token = create_access_token(identity=user.email, additional_claims=claims)

    return jsonify(accessToken=access_token)


@application.route("/delete", methods=["POST"])
@jwt_required()
def deleteUser():
    email = get_jwt_identity()

    user = User.query.filter(User.email == email).first()

    if not user:
        return {"message": "Unknown user."}, 400

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    application.run(host="0.0.0.0", debug=True)
