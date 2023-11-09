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

# orderContract = web3.eth.contract(bytecode=bytecode, abi=abi)

# -------------


@application.route("/orders_to_deliver", methods=["GET"])
@role_check("courier")
def orders_to_deliver():
    orders = []
    for o in Order.query.filter(Order.status == "CREATED").all():
        orders.append({"id": o.id, "email": o.customer_email})
    return {"orders": orders}, 200


@application.route("/pick_up_order", methods=["POST"])
@role_check("courier")
def pick_up_order():
    request_body = request.get_json()

    if "id" not in request_body:
        return {"message": "Missing order id."}, 400

    id = request_body["id"]
    if not isinstance(id, int) or id <= 0:
        return {"message": "Invalid order id."}, 400

    order = Order.query.filter(Order.id == id).first()

    if not order:
        return {"message": "Invalid order id."}, 400
    
    if not order.status == "CREATED":
        return {"message": "Invalid order id."}, 400

    # blockchain

    try:
        if "address" not in request_body or request_body["address"] == "":
            return {"message": "Missing address."}, 400

        courierAddress = request_body["address"]
        if not web3.is_checksum_address(courierAddress):
            return {"message": "Invalid address."}, 400

        balance_wei = web3.eth.get_balance(order.contract_address)
        if balance_wei < int(order.total_price):
            return {"message": "Transfer not complete."}, 400
        
        contract = web3.eth.contract(address=order.contract_address, abi=abi)

        transaction_hash = contract.functions.pick_up_order(courierAddress).transact(
            {
                "from": ownerAddress,
                "nonce": web3.eth.get_transaction_count(ownerAddress),
                "gasPrice": 21000,
            }
        )

    except ContractPanicError as error:
        print(error.data)
        return {"message": "Transfer not complete."}, 400
    except ContractLogicError as error:
        print(error.data)
        return {"message": "Transfer not complete."}, 400
    except:
        return {"message": "Ne radi blockchain lepo"}, 400

    # ---------

    order.status = "PENDING"
    database.session.commit()
    return Response(status=200)

    return {"message": "Invalid order id."}, 400


if __name__ == "__main__":
    application.run(host="0.0.0.0", debug=True, port=5003)
