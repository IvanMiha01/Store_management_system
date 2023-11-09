from flask import Flask
from flask import request, jsonify
import json

application = Flask ( __name__ )

import os
import subprocess

@application.route ( "/category_statistics", methods=["GET"] )
def category_statistics ( ):
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/category_statistics.py"

    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"
     

    result = subprocess.check_output ( ["/template.sh"] )

    retval = []
    with open("category_statistics_result", "r") as f:
        for line in f:
            retval.append(line.strip())
    
    return jsonify({"statistics":retval})

@application.route ( "/product_statistics", methods=["GET"] )
def products_statistics ( ):
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/product_statistics.py"

    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"
     
    result = subprocess.check_output ( ["/template.sh"] )
    
    retval = None
    with open("product_statistics_result", "r") as f:
        retval = json.loads(f.read())

    return jsonify({"statistics":retval})

if ( __name__ == "__main__" ):
    application.run ( host = "0.0.0.0", port=5004)