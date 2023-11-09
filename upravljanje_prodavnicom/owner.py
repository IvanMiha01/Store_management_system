from flask import Flask
from flask import request, Response
from flask import jsonify

from sqlalchemy import and_

from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import get_jwt

from configuration import Configuration

from models import database
from models import Product, Category, ProductCategory, Order, OrderProduct

from decorators import role_check

import requests

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
jwt = JWTManager(application)


@application.route("/update", methods=["POST"])
@role_check(role="owner")
def update():
    content = request.files.get("file", None)
    if content is None:
        return {"message": "Field file is missing."}, 400

    lines = content.stream.read().decode()

    i = 0
    for line in lines.split("\n"):
        fields = line.split(",")

        if len(fields) != 3:
            return {"message": f"Incorrect number of values on line {i}."}, 400

        categories = fields[0].split("|")
        name = fields[1]
        try:
            price = float(fields[2])
        except:
            return {"message": f"Incorrect price on line {i}."}, 400

        if price <= 0:
            return {"message": f"Incorrect price on line {i}."}, 400

        if Product.query.filter(Product.name == name).first():
            return {"message": f"Product {name} already exists."}, 400

        i = i + 1

    for line in lines.split("\n"):
        fields = line.split(",")
        categories = fields[0].split("|")
        name = fields[1]
        price = float(fields[2])

        p = Product(name=name, price=price)
        database.session.add(p)
        database.session.flush()

        pid = Product.query.filter(Product.name == name).first().id

        for category in categories:
            if not Category.query.filter(Category.name == category).first():
                c = Category(name=category)
                database.session.add(c)
                database.session.flush()

            cid = Category.query.filter(Category.name == category).first().id
            pc = ProductCategory(productId=pid, categoryId=cid)
            database.session.add(pc)

        database.session.flush()

    database.session.commit()

    return Response(status=200)


@application.route("/product_statistics", methods=["GET"])
@role_check(role="owner")
def product_statistics():
    # products = Product.query.all()
    # statistics = []

    # for product in products:
    #     sold_count = 0
    #     waiting_count = 0

    #     for order in product.orders:
    #         if order.status == "COMPLETE":
    #             sold_count += OrderProduct.query.filter(and_(OrderProduct.orderId == order.id, OrderProduct.productId == product.id ) ).first().quantity

    #         else:
    #             waiting_count += OrderProduct.query.filter(and_(OrderProduct.orderId == order.id, OrderProduct.productId == product.id ) ).first().quantity

    #     if sold_count > 0 or waiting_count > 0:
    #         statistics.append({
    #             "name": product.name,
    #             "sold": sold_count,
    #             "waiting": waiting_count
    #         })

    # return jsonify({"statistics": statistics})

    url = "http://sparkapp:5004/product_statistics"

    response = requests.get(url)

    if response.ok:
        try:
            data = response.json()
            return jsonify(data)
        except ValueError as e:
            return f"Invalid JSON response: {e}"
    else:
        return f"Request failed with status code: {response.status_code}"


@application.route("/category_statistics", methods=["GET"])
@role_check("owner")
def category_statistics():
    # statistics = {}
    # for c in Category.query.all():
    #     statistics[c.name] = 0

    # orders = Order.query.filter(Order.status == "COMPLETE").all()

    # for order in orders:
    #     for product in order.products:
    #         for category in product.categories:
    #             statistics[category.name] += OrderProduct.query.filter(and_(OrderProduct.orderId == order.id, OrderProduct.productId == product.id ) ).first().quantity

    # return jsonify({"statistics":sorted(statistics, key=lambda x: (-statistics[x], x))})

    url = "http://sparkapp:5004/category_statistics"

    response = requests.get(url)

    if response.ok:
        try:
            data = response.json()
            return jsonify(data)
        except ValueError as e:
            return f"Invalid JSON response: {e}"
    else:
        return f"Request failed with status code: {response.status_code}"


if __name__ == "__main__":
    application.run(host="0.0.0.0", debug=True, port=5001)
