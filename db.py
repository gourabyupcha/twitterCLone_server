# db.py

import logging
logging.basicConfig(level=logging.DEBUG)

from pymongo import MongoClient
import os, certifi
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from .env file

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"), 
    tls=True,
    tlsAllowInvalidCertificates=False,
    tlsCAFile=certifi.where())
db = client["twitter_clone_db"] 

# Export collections
users_collection = db["users"]
tweets_collection = db["tweets"]
