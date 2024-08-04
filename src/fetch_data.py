# src/fetch_data.py

import requests
import logging
from config.settings import RIOT_API_BASE_URL, RIOT_API_KEY

# Set up logging
logging.basicConfig(filename='logs/app.log', level=logging.DEBUG)

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
        logging.info(f"Fetched data for match {match_id}: {response.status_code}")
        logging.debug(f"Response content: {response.text}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred for match {match_id}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Error occurred for match {match_id}: {err}")
    return None
