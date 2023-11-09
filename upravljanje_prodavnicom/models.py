from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "productcategory"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(
        database.Integer, database.ForeignKey("products.id"), nullable=False
    )
    categoryId = database.Column(
        database.Integer, database.ForeignKey("categories.id"), nullable=False
    )


class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)

    products = database.relationship(
        "Product", secondary=ProductCategory.__table__, back_populates="categories"
    )


class OrderProduct(database.Model):
    __tablename__ = "orderproduct"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(
        database.Integer, database.ForeignKey("products.id"), nullable=False
    )
    orderId = database.Column(
        database.Integer, database.ForeignKey("orders.id"), nullable=False
    )
    quantity = database.Column(database.Integer, nullable=False)


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    price = database.Column(database.Float, nullable=False)

    categories = database.relationship(
        "Category", secondary=ProductCategory.__table__, back_populates="products"
    )

    orders = database.relationship(
        "Order", secondary=OrderProduct.__table__, back_populates="products"
    )


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key=True)
    customer_email = database.Column(database.String(256), nullable=False)
    total_price = database.Column(database.Float, nullable=False)
    status = database.Column(database.String(20), nullable=False)
    timestamp = database.Column(
        database.DateTime, nullable=False, default=database.func.now()
    )

    products = database.relationship(
        "Product", secondary=OrderProduct.__table__, back_populates="orders"
    )

    contract_address = database.Column(database.String(256), nullable=False)
