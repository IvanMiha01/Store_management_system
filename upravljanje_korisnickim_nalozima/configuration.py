import os
from datetime import timedelta

# DATABASE_URL = "database" if ( "PRODUCTION" in os.environ ) else "localhost"
DATABASE_URL = "databaseAuth" if ( "PRODUCTION" in os.environ ) else "localhost"

class Configuration:
    SQLALCHEMY_DATABASE_URI   = f"mysql://root:root@{DATABASE_URL}/users"
    JWT_SECRET_KEY            = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta ( minutes = 60 )
    