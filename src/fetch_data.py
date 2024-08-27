# src/fetch_data.py

import requests
import logging
import os
from config.settings import RIOT_API_BASE_URL, RIOT_API_KEY

# Set up logging with UTF-8 encoding
log_file = 'logs/app.log'
log_dir = os.path.dirname(log_file)

# Ensure the log directory exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging with a file handler that supports UTF-8 encoding
file_handler = logging.FileHandler(log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Set up the logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def get_match_data(game_id, platform="EUW1"):
    """Fetch match data from the Riot API using the GameId."""
    match_id = f"{platform}_{game_id}"
    url = f"{RIOT_API_BASE_URL}/match/v5/matches/{match_id}"
    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        logger.info(f"Fetched data for match {match_id}: {response.status_code}")
        logger.debug(f"Response content: {response.text.encode('utf-8', 'replace').decode('utf-8')}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred for match {match_id}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Error occurred for match {match_id}: {err}")
    return None
