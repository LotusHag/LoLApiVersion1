# src/process_data.py

def process_match_data(raw_data):
    """Process raw match data and extract relevant information."""
    processed_data = {
        "match_id": raw_data.get("metadata", {}).get("matchId"),
        "game_duration": raw_data.get("info", {}).get("gameDuration"),
        "game_start_timestamp": raw_data.get("info", {}).get("gameStartTimestamp"),
        "teams": [],
        "players": []  # This will hold references to Player objects
    }

    # Extract team data
    teams_info = raw_data.get("info", {}).get("teams", [])
    for team in teams_info:
        team_data = {
            "team_id": team.get("teamId"),
            "win": team.get("win"),
            "objectives": team.get("objectives"),
            "bans": [ban.get("championId") for ban in team.get("bans", [])]
        }
        processed_data["teams"].append(team_data)

    # Extract player data
    participants = raw_data.get("info", {}).get("participants", [])
    for participant in participants:
        player_data = {
            "summoner_name": participant.get("summonerName"),
            "summoner_id": participant.get("summonerId"),
            "champion_id": participant.get("championId"),
            "champion_name": participant.get("championName"),
            "individual_position": participant.get("individualPosition"),  # Only keep individual_position
            "team_id": participant.get("teamId"),

            # Combat stats
            "kills": participant.get("kills"),
            "deaths": participant.get("deaths"),
            "assists": participant.get("assists"),
            "total_damage_dealt_to_champions": participant.get("totalDamageDealtToChampions"),
            "total_damage_taken": participant.get("totalDamageTaken"),
            "damage_dealt_to_turrets": participant.get("damageDealtToTurrets"),
            "damage_dealt_to_objectives": participant.get("damageDealtToObjectives"),

            # Economy stats
            "gold_earned": participant.get("goldEarned"),
            "total_minions_killed": participant.get("totalMinionsKilled"),

            # Vision and warding stats
            "vision_score": participant.get("visionScore"),
            "wards_placed": participant.get("wardsPlaced"),
            "wards_killed": participant.get("wardsKilled"),
            "vision_wards_placed": participant.get("visionWardsPlaced"),

            # Utility stats
            "time_ccing_others": participant.get("timeCCingOthers"),
            "total_heal": participant.get("totalHeal"),

            # Multi-kill stats
            "double_kills": participant.get("doubleKills"),
            "triple_kills": participant.get("tripleKills"),
            "quadra_kills": participant.get("quadraKills"),
            "penta_kills": participant.get("pentaKills")
        }
        processed_data["players"].append(player_data)

    return processed_data
