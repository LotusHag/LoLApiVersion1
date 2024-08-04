# src/store_data.py

from pymongo import MongoClient
from config.settings import MONGO_URI, MONGO_DB

def get_database():
    """Connect to MongoDB and return the database object."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db

def store_match_data(processed_data):
    """Store processed match data in MongoDB."""
    db = get_database()
    matches_collection = db["matches"]
    # Insert the match data into the collection
    matches_collection.insert_one(processed_data)
