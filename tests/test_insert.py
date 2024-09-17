# test_insert.py

from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "lol_matches"  # Replace with your actual database name if different
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

try:
    # Try inserting a test document
    test_collection = db['test_collection']
    test_collection.insert_one({"test_key": "test_value"})
    print("Test document inserted successfully.")
    print("Current collections:", db.list_collection_names())
except Exception as e:
    print("Error inserting test document:", e)
