# backend/database.py

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is not set in .env")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client

def get_users():
    return _get_client()["study_agent"]["users"]
