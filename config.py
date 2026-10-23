"""
config.py
---------
Loads environment variables from .env and exposes them as a Python class.
Flask reads this class when the app starts up.
"""

import os
from dotenv import load_dotenv

# Load the .env file so os.environ can see its values
load_dotenv()


class Config:
    # Secret key is used to sign session cookies — keep it secret!
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-dev-key")

    # MongoDB connection string
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/expense_tracker")

    # Name of the MongoDB database parsed from the URI or fallback
    MONGO_DBNAME = (
        os.environ.get("MONGO_DBNAME")
        or (
            MONGO_URI.split("/")[-1].split("?")[0]
            if ("/" in MONGO_URI and MONGO_URI.split("/")[-1].split("?")[0])
            else "expense_tracker"
        )
    )
