from pyspark.sql import SparkSession
from flask import jsonify

import os

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = (
    os.environ["DATABASE_IP"] if ("DATABASE_IP" in os.environ) else "localhost"
)

builder = SparkSession.builder.appName("PySpark Category Statistics")

if not PRODUCTION:
    builder = builder.master("local[*]").config(
        "spark.driver.extraClassPath", "mysql-connector-j-8.0.33.jar"
    )


spark = builder.getOrCreate()

orders_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store")
    .option("dbtable", "store.orders")
    .option("user", "root")
    .option("password", "root")
    .load()
)

orderproduct_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store")
    .option("dbtable", "store.orderproduct")
    .option("user", "root")
    .option("password", "root")
    .load()
)

products_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store")
    .option("dbtable", "store.products")
    .option("user", "root")
    .option("password", "root")
    .load()
)

productcategory_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store")
    .option("dbtable", "store.productcategory")
    .option("user", "root")
    .option("password", "root")
    .load()
)

category_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store")
    .option("dbtable", "store.categories")
    .option("user", "root")
    .option("password", "root")
    .load()
)


result = (
    orders_data_frame.filter(orders_data_frame["status"]=="COMPLETE")
                     .join(orderproduct_data_frame, orderproduct_data_frame["orderId"] == orders_data_frame["id"])
                     .join(productcategory_data_frame, orderproduct_data_frame["productId"] == productcategory_data_frame["productId"])
                     .join(category_data_frame, productcategory_data_frame["categoryId"] == category_data_frame["id"], "right")
                     .groupBy("name")
                     .sum("quantity")
                     .collect()
)

statistics = {}

for r in result:
    if r["sum(quantity)"] is None:
        statistics[r["name"]] = 0
    else:
        statistics[r["name"]] = r["sum(quantity)"]

    
with open("category_statistics_result", "w") as f:
    for c in sorted(statistics, key=lambda x: (-statistics[x], x)):
        f.write(c + '\n')

spark.stop()
