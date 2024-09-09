# src/store_data.py

from pymongo import MongoClient
from config.settings import MONGO_URI, MONGO_DB

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
            "past_roster": [],
            "match_history": []
        }
        team_id = teams_collection.insert_one(team).inserted_id
        team["_id"] = team_id
    else:
        team_id = team["_id"]
    
    return team

def get_or_create_player(db, summoner_id, summoner_name):
    """Retrieve or create a player in the database."""
    players_collection = db["players"]

    # Ensure summoner_id is stored as a string, not ObjectId
    if not isinstance(summoner_id, str):
        print(f"Error: summoner_id is not a string: {summoner_id}")
        return None

    # Try to find player by summoner_id
    player = players_collection.find_one({"summoner_ids": summoner_id})

    # Debugging output to track player creation and field types
    print(f"Checking player in DB with summoner_id: {summoner_id}, summoner_name: {summoner_name}")
    print(f"Player found: {player}")

    if not player:
        # Creating new player with correct summoner_ids field format
        player = {
            "summoner_ids": [summoner_id],  # Ensure this is always a list
            "summoner_names": [summoner_name],
            "current_teams": [],
            "past_teams": [],
            "match_history": [],
            "average_stats": {},
            "champions_played": {}
        }
        player_id = players_collection.insert_one(player).inserted_id
        player["_id"] = player_id
        print(f"New player created: {player}")  # Debug: Show player details when created
    else:
        if summoner_name not in player["summoner_names"]:
            player["summoner_names"].append(summoner_name)
            players_collection.update_one({"_id": player["_id"]}, {"$set": {"summoner_names": player["summoner_names"]}})
        print(f"Existing player found: {player}")  # Debug: Show player details if found
    
    return player

def update_player(db, player, match_id, team_id, stats):
    """Update the player with new match, team, and stats information."""
    players_collection = db["players"]
    
    # Update match history with match ID only
    player["match_history"].append(match_id)
    
    # Update teams
    if team_id not in player["current_teams"]:
        player["past_teams"].extend([t for t in player["current_teams"] if t not in player["past_teams"]])
        player["current_teams"].append(team_id)
    
    # Update average stats
    total_games = len(player["match_history"])
    for key, value in stats.items():
        if key in [
            "kills", "deaths", "assists", "total_damage_dealt_to_champions",
            "total_damage_taken", "damage_dealt_to_turrets", "damage_dealt_to_objectives",
            "gold_earned", "total_minions_killed", "vision_score", "wards_placed", 
            "wards_killed", "vision_wards_placed", "time_ccing_others", "total_heal",
            "double_kills", "triple_kills", "quadra_kills", "penta_kills"
        ]:
            if key not in player["average_stats"]:
                player["average_stats"][key] = value
            else:
                try:
                    player["average_stats"][key] = ((float(player["average_stats"][key]) * (total_games - 1)) + float(value)) / total_games
                except (TypeError, ValueError):
                    player["average_stats"][key] = value
    
    # Update champions played
    champion_name = stats.get("championName")
    if champion_name:
        if champion_name not in player["champions_played"]:
            player["champions_played"][champion_name] = 1
        else:
            player["champions_played"][champion_name] += 1
    
    players_collection.update_one({"_id": player["_id"]}, {"$set": player})

def store_match_data(db, processed_data, division, split, match_type, blue_team_name, red_team_name):
    """Store the entire match data from the Riot API response in MongoDB without filtering any fields."""
    matches_collection = db["matches"]
    
    # Debugging output to check what is being stored
    print(f"Storing match data: {processed_data}")

    # Store match data and get its ID
    match = {
        "match_id": processed_data["metadata"]["matchId"],
        "division": division,
        "split": split,
        "match_type": match_type,
        "teams": [blue_team_name, red_team_name],
        "players": [],  # Will store references to Player objects
        "data": processed_data  # Store all the data without filtering
    }
    match_id = matches_collection.insert_one(match).inserted_id

    # Process teams
    blue_team = get_or_create_team(db, blue_team_name, division, split)
    red_team = get_or_create_team(db, red_team_name, division, split)

    # Process players and build current roster lists
    blue_team_roster = []
    red_team_roster = []

    for participant in processed_data["info"]["participants"]:
        # Retrieve or create player with debug information
        player = get_or_create_player(db, participant["summonerId"], participant["summonerName"])
        print(f"Processing player: {participant['summonerName']} with ID: {participant['summonerId']}")

        team_id = blue_team["_id"] if participant["teamId"] == 100 else red_team["_id"]
        update_player(db, player, match_id, team_id, participant)
        
        # Link player object to match
        match["players"].append(player["_id"])

        # Assign player to the correct team roster
        if participant["teamId"] == 100:  # Assuming team_id 100 is blue team
            blue_team_roster.append(participant)
        elif participant["teamId"] == 200:  # Assuming team_id 200 is red team
            red_team_roster.append(participant)
    
    # Update match document with player links
    matches_collection.update_one({"_id": match_id}, {"$set": {"players": match["players"]}})
    
    # Update teams with the new match and roster information
    update_team(db, blue_team, match_id, blue_team_roster)
    update_team(db, red_team, match_id, red_team_roster)

def update_team(db, team, match_id, current_roster):
    """Update the team with new match and roster information."""
    teams_collection = db["teams"]
    
    # Update match history
    team["match_history"].append(match_id)
    
    # Update roster
    new_roster_ids = [player["summonerId"] for player in current_roster]
    for player_id in new_roster_ids:
        if player_id not in team["current_roster"]:
            team["past_roster"].extend([p for p in team["current_roster"] if p not in team["past_roster"]])
            team["current_roster"] = new_roster_ids
    
    teams_collection.update_one({"_id": team["_id"]}, {"$set": team})
