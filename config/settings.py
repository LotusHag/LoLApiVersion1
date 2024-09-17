# config/settings.py

import os
from config.api_keys import RIOT_API_KEY

# General settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# MongoDB settings
MONGO_URI = "mongodb://localhost:27017/"  # Ensure this is correct
MONGO_DB = "lol_matches"  # Make sure this is the correct database name

# Riot API settings
RIOT_API_BASE_URL = "https://europe.api.riotgames.com/lol"
RIOT_API_KEY = RIOT_API_KEY
