from pyspark.sql import SparkSession
from flask import jsonify
import json

import os

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = (
    os.environ["DATABASE_IP"] if ("DATABASE_IP" in os.environ) else "localhost"
)

builder = SparkSession.builder.appName("PySpark Product Statistics")

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


result = (
    orders_data_frame.join(orderproduct_data_frame, orderproduct_data_frame["orderId"] == orders_data_frame["id"])
                     .join(products_data_frame, orderproduct_data_frame["productId"] == products_data_frame["id"])
                     .groupBy("name", "status")
                     .sum("quantity")
                     .collect()
)

statistics = {}

for r in result:
    if r["name"] not in statistics:
        statistics[r["name"]] = {"sold": 0, "waiting": 0}
    if r["status"] == "COMPLETE":
        statistics[r["name"]]["sold"] += r["sum(quantity)"]
    else:
        statistics[r["name"]]["waiting"] += r["sum(quantity)"]

retval = []
for s in sorted(statistics.keys(), key= lambda x: (x)):
    retval.append({
        "name": s,
        "sold": statistics[s]["sold"],
        "waiting": statistics[s]["waiting"]
    })

with open("product_statistics_result", "w") as f:
    for i in json.dumps(retval):
        f.write(i)

spark.stop()
