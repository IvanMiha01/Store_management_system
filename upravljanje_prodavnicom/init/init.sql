create database store;
use store;

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(256) NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(256) NOT NULL UNIQUE,
    price FLOAT NOT NULL
);

CREATE TABLE productcategory (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    productId INTEGER NOT NULL,
    categoryId INTEGER NOT NULL,
    FOREIGN KEY (productId) REFERENCES products (id),
    FOREIGN KEY (categoryId) REFERENCES categories (id)
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_email VARCHAR(256) NOT NULL,
    total_price FLOAT NOT NULL,
    status VARCHAR(256) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    contract_address VARCHAR(256) NOT NULL
);

CREATE TABLE orderproduct (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    productId INTEGER NOT NULL,
    orderId INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (productId) REFERENCES products (id),
    FOREIGN KEY (orderId) REFERENCES orders (id)
);
