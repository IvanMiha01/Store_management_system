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

import json

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
jwt = JWTManager(application)

# blockchain

from web3 import Web3
from web3 import HTTPProvider
from web3.exceptions import ContractLogicError, ContractPanicError
from web3 import Account

web3 = Web3(HTTPProvider("http://ganache:8545"))


def read_file(path):
    with open(path, "r") as file:
        return file.read()


abi = read_file("./OrderContract.abi")
bytecode = read_file("./OrderContract.bin")

ownerAddress = web3.eth.accounts[0]

orderContract = web3.eth.contract(bytecode=bytecode, abi=abi)

# -------------


@application.route("/search", methods=["GET"])
@role_check("customer")
def search():
    # products = []
    # if "name" in request.args:
    #     name = request.args["name"]
    #     products = Product.query.filter(Product.name.like(f"%{name}%")).all()
    # else:
    #     products = Product.query.all()

    # categories = []
    # if "category" in request.args:
    #     category = request.args["category"]
    #     categories = Category.query.filter(Category.name.like(f"%{category}%")).all()
    # else:
    #     categories = Category.query.all()

    # filtered_products = []
    # filtered_categories = set()
    # for product in products:
    #     if set(categories).intersection(product.categories):
    #         filtered_products.append(
    #             {
    #                 "categories": [c.name for c in product.categories],
    #                 "id": product.id,
    #                 "name": product.name,
    #                 "price": product.price,
    #             }
    #         )
    #         for c in product.categories:
    #             if "category" in request.args:
    #                 category = request.args["category"]
    #                 if c.name.find(category) != -1:
    #                     filtered_categories.add(c.name)
    #             else:
    #                 filtered_categories.add(c.name)

    # return jsonify(
    #     {"categories": list(filtered_categories), "products": filtered_products}
    # )

    products = Product.query
    categories = Category.query

    if "name" in request.args:
        name = request.args["name"]
        products = products.filter(Product.name.ilike(f"%{name}%"))

    if "category" in request.args:
        category = request.args["category"]
        categories = categories.filter(Category.name.ilike(f"%{category}%"))

    filtered_products = (
        products.join(Product.categories)
        .filter(Category.id.in_([c.id for c in categories]))
        .all()
    )

    filtered_categories = set(category.name for product in filtered_products for category in product.categories)

    result = {
        "categories": list(filtered_categories),
        "products": [
            {
                "categories": [c.name for c in product.categories],
                "id": product.id,
                "name": product.name,
                "price": product.price,
            }
            for product in filtered_products
        ]
    }

    return jsonify(result)


@application.route("/order", methods=["POST"])
@role_check("customer")
def order():
    request_body = request.get_json()

    if "requests" not in request_body:
        return {"message": "Field requests is missing."}, 400

    requests = request_body["requests"]

    i = 0
    total_price = 0
    for r in requests:
        if "id" not in r:
            return {"message": f"Product id is missing for request number {i}."}, 400
        if "quantity" not in r:
            return {
                "message": f"Product quantity is missing for request number {i}."
            }, 400

        id = r["id"]
        if not isinstance(id, int) or id <= 0:
            return {"message": f"Invalid product id for request number {i}."}, 400

        quantity = r["quantity"]
        if not isinstance(quantity, int) or quantity <= 0:
            return {"message": f"Invalid product quantity for request number {i}."}, 400

        p = Product.query.filter(Product.id == id).first()
        if not p:
            return {"message": f"Invalid product for request number {i}."}, 400

        total_price += p.price * quantity
        i += 1

    # blockchain

    try:
        if "address" not in request_body or request_body["address"] == "":
            return {"message": "Field address is missing."}, 400

        customerAddress = request_body["address"]
        if not web3.is_checksum_address(customerAddress):
            return {"message": "Invalid address."}, 400

        transaction_hash = orderContract.constructor(
            customerAddress, int(total_price)
        ).transact(
            {
                "from": ownerAddress,
                "nonce": web3.eth.get_transaction_count(ownerAddress),
                "gasPrice": 21000,
            }
        )

        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
        contract_address = receipt.contractAddress

    except ContractPanicError as error:
        return {"message": error.data}, 400
    except ContractLogicError as error:
        return {"message": error.message}, 400
    except:
        return {"message": "Ne radi blockchain lepo"}, 400

    # ---------

    order = Order(
        customer_email=get_jwt_identity(),
        total_price=total_price,
        status="CREATED",
        contract_address=contract_address,
    )
    database.session.add(order)
    database.session.commit()

    for r in requests:
        op = OrderProduct(productId=r["id"], orderId=order.id, quantity=r["quantity"])
        database.session.add(op)

    database.session.commit()

    return {"id": order.id}, 200


@application.route("/status", methods=["GET"])
@role_check("customer")
def status():
    orders = []
    for o in Order.query.filter(Order.customer_email == get_jwt_identity()).all():
        products = []
        for p in o.products:
            products.append(
                {
                    "categories": [c.name for c in p.categories],
                    "name": p.name,
                    "price": p.price,
                    "quantity": OrderProduct.query.filter(
                        and_(
                            OrderProduct.orderId == o.id, OrderProduct.productId == p.id
                        )
                    )
                    .first()
                    .quantity,
                }
            )
        orders.append(
            {
                "products": products,
                "price": o.total_price,
                "status": o.status,
                "timestamp": o.timestamp.isoformat(),
            }
        )

    return {"orders": orders}, 200


@application.route("/delivered", methods=["POST"])
@role_check("customer")
def delivered():
    request_body = request.get_json()

    if "id" not in request_body:
        return {"message": "Missing order id."}, 400

    id = request_body["id"]
    if not isinstance(id, int) or id <= 0:
        return {"message": "Invalid order id."}, 400

    order = Order.query.filter(Order.id == id).first()

    if not order:
        return {"message": "Invalid order id."}, 400

    if not order.status == "PENDING":
        return {"message": "Invalid order id."}, 400

    if "keys" not in request_body or request_body["keys"] == "":
        return {"message": "Missing keys."}, 400

    if "passphrase" not in request_body or request_body["passphrase"] == "":
        return {"message": "Missing passphrase."}, 400

    # blockchain

    customer_private_key = None
    try:
        customer_private_key = Account.decrypt(json.loads(request_body["keys"].replace("'",'"')), request_body["passphrase"])
    except ValueError:
        return {"message": "Invalid credentials."}, 400

    try:
        keys = json.loads(request_body["keys"].replace("'",'"'))
        customer_address = web3.to_checksum_address(keys["address"])

        contract = web3.eth.contract(address=order.contract_address, abi=abi)

        transaction = contract.functions.delivered().build_transaction(
            {
                "from": customer_address,
                "nonce": web3.eth.get_transaction_count(customer_address),
                "gasPrice": 21000,
            }
        )

        signed_transaction = web3.eth.account.sign_transaction(
            transaction, customer_private_key
        )
        transaction_hash = web3.eth.send_raw_transaction(
            signed_transaction.rawTransaction
        )
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    except ContractPanicError as error:
        if "Invalid customer account" in error.message:
            return {"message": "Invalid customer account."}, 400
        if "Transfer not complete." in error.message:
            return {"message": "Transfer not complete."}, 400
        return {"message": error.message}, 400 
    except ContractLogicError as error:
        if "Invalid customer account" in error.message:
            return {"message": "Invalid customer account."}, 400
        if "Transfer not complete." in error.message:
            return {"message": "Transfer not complete."}, 400
        return {"message": error.message}, 400 

    order.status = "COMPLETE"
    database.session.commit()
    return Response(status=200)


@application.route("/pay", methods=["POST"])
@role_check("customer")
def pay():
    request_body = request.get_json()

    if "id" not in request_body:
        return {"message": "Missing order id."}, 400

    id = request_body["id"]
    if not isinstance(id, int) or id <= 0:
        return {"message": "Invalid order id."}, 400

    order = Order.query.filter(Order.id == id).first()
    if not order:
        return {"message": "Invalid order id."}, 400

    if "keys" not in request_body or request_body["keys"] == "":
        return {"message": "Missing keys."}, 400

    if "passphrase" not in request_body or request_body["passphrase"] == "":
        return {"message": "Missing passphrase."}, 400

    # blockchain

    customer_private_key = None
    try:
        customer_private_key = Account.decrypt(
            request_body["keys"], request_body["passphrase"]
        )
    except:
        return {"message": "Invalid credentials."}, 400

    try:
        keys = json.loads(request_body["keys"])
        customer_address = web3.to_checksum_address(keys["address"])

        balance_wei = web3.eth.get_balance(customer_address)
        if balance_wei < int(order.total_price):
            return {"message": "Insufficient funds."}, 400

        if not order.status == "CREATED":
            return {"message": "Transfer already complete."}, 400

        contract_balance_wei = web3.eth.get_balance(order.contract_address)
        if contract_balance_wei > 0:
            return {"message": "Transfer already complete."}, 400

        contract = web3.eth.contract(address=order.contract_address, abi=abi)

        transaction = contract.functions.pay().build_transaction(
            {
                "from": customer_address,
                "nonce": web3.eth.get_transaction_count(customer_address),
                "gasPrice": 21000,
                "value": int(order.total_price),
            }
        )

        signed_transaction = web3.eth.account.sign_transaction(
            transaction, customer_private_key
        )
        transaction_hash = web3.eth.send_raw_transaction(
            signed_transaction.rawTransaction
        )
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    except ContractPanicError as error:
        return {"message": error.data}, 400
    except ContractLogicError as error:
        return {"message": error.data}, 400

    # ------------

    return Response(200)


if __name__ == "__main__":
    application.run(host="0.0.0.0", debug=True, port=5002)
