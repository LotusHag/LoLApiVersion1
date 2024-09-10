# src/store_data.py

from pymongo import MongoClient
from config.settings import MONGO_URI, MONGO_DB
from bson.objectid import ObjectId

def get_database():
    """Connect to MongoDB and return the database object."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db

def get_or_create_team(db, team_name, division, split):
    """Retrieve or create a team in the database."""
    teams_collection = db["teams"]
    team = teams_collection.find_one({"team_name": team_name, "division": division, "split": split})
    
    if not team:
        team = {
            "team_name": team_name,
            "organisation": None,
            "split": split,
            "division": division,
            "current_roster": [],
            "match_history": [],
            "stats_totals": {},  # Store total stats here
            "champions_played": {},  # Track the number of times each champion is played
            "players_played": {},  # Track the players who have played for the team with counts
            "bans_against": {},  # Track the number of times champions are banned against the team
            "bans_made": {}  # Track the number of times the team has banned champions
        }
        team_id = teams_collection.insert_one(team).inserted_id
        team["_id"] = team_id
    else:
        team_id = team["_id"]
    
    return team

def get_or_create_player(db, summoner_id, summoner_name, riot_id_name, riot_id_tagline):
    """Retrieve or create a player in the database."""
    players_collection = db["players"]

    if not isinstance(summoner_id, str):
        print(f"Error: summoner_id is not a string: {summoner_id}")
        return None

    player = players_collection.find_one({"summoner_ids": summoner_id})

    # Combine riot_id_name and riot_id_tagline to create a unique identifier string
    riot_id_pair = f"{riot_id_name}#{riot_id_tagline}"

    if not player:
        player = {
            "summoner_ids": [summoner_id],
            "summoner_names": [summoner_name],
            "riotIDPairs": [riot_id_pair] if riot_id_name and riot_id_tagline else [],
            "current_teams": [],
            "match_history": [],
            "stats_totals": {},
            "champions_played": {},
            "positions_played": {}
        }
        player_id = players_collection.insert_one(player).inserted_id
        player["_id"] = player_id
        print(f"New player created: {player}")
    else:
        if summoner_name not in player["summoner_names"]:
            player["summoner_names"].append(summoner_name)
        
        # Only add the riot_id_pair if it's valid and not already in the list
        if riot_id_name and riot_id_tagline and riot_id_pair not in player.get("riotIDPairs", []):
            player.setdefault("riotIDPairs", []).append(riot_id_pair)

        players_collection.update_one(
            {"_id": player["_id"]}, 
            {"$set": {
                "summoner_names": player["summoner_names"],
                "riotIDPairs": player["riotIDPairs"]
            }}
        )
        print(f"Existing player updated: {player}")
    
    return player

def update_player(db, player, match_id, team_id, stats):
    """Update the player with new match, team, and stats information."""
    players_collection = db["players"]
    
    player["match_history"].append(match_id)
    
    if team_id not in player["current_teams"]:
        player["current_teams"].append(team_id)

    # Filter out unnecessary stats like items and profile icon
    filtered_stats = {k: v for k, v in stats.items() if k not in {"items", "profileIcon"}}

    for key, value in filtered_stats.items():
        if key not in {"championName", "individualPosition", "lane", 
                       "role", "summonerId", "summonerName", "teamPosition", 
                       "puuid", "item0", "item1", "item2", "item3", "item4", "item5",
                       "item6", "playerAugment1", "playerAugment2", "playerAugment3",
                       "playerAugment4", "playerAugment5", "playerAugment6", "playerSubteamId", "riotIdGameName", "riotIdTagline"}:
            if key not in player["stats_totals"]:
                player["stats_totals"][key] = value
            else:
                try:
                    player["stats_totals"][key] += value
                except (TypeError, ValueError):
                    player["stats_totals"][key] = value
    
    champion_name = stats.get("championName")
    if champion_name:
        if champion_name not in player["champions_played"]:
            player["champions_played"][champion_name] = 1
        else:
            player["champions_played"][champion_name] += 1
    
    position = stats.get("individualPosition")
    if position:
        if position not in player["positions_played"]:
            player["positions_played"][position] = 1
        else:
            player["positions_played"][position] += 1
    
    players_collection.update_one({"_id": player["_id"]}, {"$set": player})

def store_match_data(db, processed_data, division, split, match_type, blue_team_name, red_team_name):
    """Store the entire match data from the Riot API response in MongoDB without filtering any fields."""
    matches_collection = db["matches"]
    
    print(f"Storing match data: {processed_data}")

    match = {
        "match_id": processed_data["metadata"]["matchId"],
        "division": division,
        "split": split,
        "match_type": match_type,
        "teams": [blue_team_name, red_team_name],
        "players": [],
        "data": processed_data
    }
    match_id = matches_collection.insert_one(match).inserted_id

    blue_team = get_or_create_team(db, blue_team_name, division, split)
    red_team = get_or_create_team(db, red_team_name, division, split)

    blue_team_roster = []
    red_team_roster = []
    blue_team_stats = {}
    red_team_stats = {}

    for participant in processed_data["info"]["participants"]:
        # Extract riotIDGameName and riotIDTagline directly from the API data
        riot_id_name = participant.get("riotIdGameName", "")
        riot_id_tagline = participant.get("riotIdTagline", "")
        
        player = get_or_create_player(db, participant["summonerId"], participant["summonerName"], riot_id_name, riot_id_tagline)
        print(f"Processing player: {participant['summonerName']} with ID: {participant['summonerId']}")

        team_id = blue_team["_id"] if participant["teamId"] == 100 else red_team["_id"]
        update_player(db, player, match_id, team_id, participant)
        
        match["players"].append(player["_id"])

        if participant["teamId"] == 100:
            blue_team_roster.append(player["_id"])
            accumulate_team_stats(blue_team_stats, participant)
            track_team_champion_and_player(blue_team, participant, player["_id"])
        elif participant["teamId"] == 200:
            red_team_roster.append(player["_id"])
            accumulate_team_stats(red_team_stats, participant)
            track_team_champion_and_player(red_team, participant, player["_id"])
    
    track_bans(processed_data, blue_team, red_team)
    
    matches_collection.update_one({"_id": match_id}, {"$set": {"players": match["players"]}})
    
    update_team(db, blue_team, match_id, blue_team_roster, blue_team_stats)
    update_team(db, red_team, match_id, red_team_roster, red_team_stats)

def accumulate_team_stats(team_stats, player_stats):
    """Accumulate player stats into team stats totals."""
    for key, value in player_stats.items():
        if key not in {"championName", "individualPosition", "lane", 
                       "role", "summonerId", "summonerName", "teamPosition", "puuid"}:
            if key not in team_stats:
                team_stats[key] = value
            else:
                try:
                    team_stats[key] += value
                except (TypeError, ValueError):
                    team_stats[key] = value

def track_team_champion_and_player(team, player_stats, player_id):
    """Track the champions and players for the team."""
    champion_name = player_stats.get("championName")
    if champion_name:
        if champion_name not in team["champions_played"]:
            team["champions_played"][champion_name] = 1
        else:
            team["champions_played"][champion_name] += 1
    
    if player_id not in team["players_played"]:
        team["players_played"][str(player_id)] = 1
    else:
        team["players_played"][str(player_id)] += 1

def track_bans(processed_data, blue_team, red_team):
    """Track bans against and made by each team."""
    teams_data = processed_data.get("info", {}).get("teams", [])
    if len(teams_data) == 2:
        # Blue Team Bans
        for ban in teams_data[0].get("bans", []):
            champion_id = ban.get("championId")
            if champion_id is not None:
                if str(champion_id) not in blue_team["bans_made"]:
                    blue_team["bans_made"][str(champion_id)] = 1
                else:
                    blue_team["bans_made"][str(champion_id)] += 1
                
                if str(champion_id) not in red_team["bans_against"]:
                    red_team["bans_against"][str(champion_id)] = 1
                else:
                    red_team["bans_against"][str(champion_id)] += 1

        # Red Team Bans
        for ban in teams_data[1].get("bans", []):
            champion_id = ban.get("championId")
            if champion_id is not None:
                if str(champion_id) not in red_team["bans_made"]:
                    red_team["bans_made"][str(champion_id)] = 1
                else:
                    red_team["bans_made"][str(champion_id)] += 1

                if str(champion_id) not in blue_team["bans_against"]:
                    blue_team["bans_against"][str(champion_id)] = 1
                else:
                    blue_team["bans_against"][str(champion_id)] += 1

def update_team(db, team, match_id, current_roster, accumulated_stats):
    """Update the team with new match, roster, and accumulated stats information."""
    teams_collection = db["teams"]
    
    team["match_history"].append(match_id)
    
    new_roster_ids = [str(player_id) for player_id in current_roster]
    team["current_roster"] = list(set(team["current_roster"] + new_roster_ids))
    
    if "stats_totals" not in team:
        team["stats_totals"] = accumulated_stats
    else:
        for key, value in accumulated_stats.items():
            if key in team["stats_totals"]:
                try:
                    team["stats_totals"][key] += value
                except (TypeError, ValueError):
                    team["stats_totals"][key] = value
            else:
                team["stats_totals"][key] = value

    teams_collection.update_one({"_id": team["_id"]}, {"$set": team})
