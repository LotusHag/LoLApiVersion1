# config/settings.py

import os
from config.api_keys import RIOT_API_KEY

# General settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# MongoDB settings
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "lol_matches"

# Riot API settings
RIOT_API_BASE_URL = "https://europe.api.riotgames.com/lol"
RIOT_API_KEY = RIOT_API_KEY
