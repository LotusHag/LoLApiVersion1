# src/analyse_data.py

from pymongo import MongoClient
from config.settings import MONGO_URI, MONGO_DB

def get_database():
    """Connect to MongoDB and return the database object."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db

def calculate_team_averages():
    """Calculate and return average statistics for teams."""
    db = get_database()
    matches_collection = db["matches"]
    pipeline = [
        {"$unwind": "$teams"},
        {"$group": {
            "_id": "$teams.team_id",
            "average_kills": {"$avg": "$teams.kills"},
            "average_deaths": {"$avg": "$teams.deaths"},
            "average_assists": {"$avg": "$teams.assists"},
            "win_rate": {"$avg": {"$cond": [{"$eq": ["$teams.win", True]}, 1, 0]}}
        }}
    ]
    team_averages = list(matches_collection.aggregate(pipeline))
    return team_averages
