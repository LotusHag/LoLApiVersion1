# src/process_data.py

def process_match_data(raw_data):
    """Process raw match data and extract relevant information."""
    processed_data = {
        "match_id": raw_data.get("metadata", {}).get("matchId"),
        "game_duration": raw_data.get("info", {}).get("gameDuration"),
        "game_start_timestamp": raw_data.get("info", {}).get("gameStartTimestamp"),
        "teams": [],
        "players": []
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
            "role": participant.get("role"),
            "lane": participant.get("lane"),
            "individual_position": participant.get("individualPosition"),
            "team_id": participant.get("teamId"),

            # Combat stats
            "kills": participant.get("kills"),
            "deaths": participant.get("deaths"),
            "assists": participant.get("assists"),
            "total_damage_dealt": participant.get("totalDamageDealt"),
            "total_damage_dealt_to_champions": participant.get("totalDamageDealtToChampions"),
            "total_damage_taken": participant.get("totalDamageTaken"),
            "physical_damage_dealt": participant.get("physicalDamageDealt"),
            "physical_damage_dealt_to_champions": participant.get("physicalDamageDealtToChampions"),
            "magic_damage_dealt": participant.get("magicDamageDealt"),
            "magic_damage_dealt_to_champions": participant.get("magicDamageDealtToChampions"),
            "true_damage_dealt": participant.get("trueDamageDealt"),
            "true_damage_dealt_to_champions": participant.get("trueDamageDealtToChampions"),
            "damage_self_mitigated": participant.get("damageSelfMitigated"),
            "damage_dealt_to_turrets": participant.get("damageDealtToTurrets"),
            "damage_dealt_to_objectives": participant.get("damageDealtToObjectives"),

            # Gold and farming stats
            "gold_earned": participant.get("goldEarned"),
            "gold_spent": participant.get("goldSpent"),
            "total_minions_killed": participant.get("totalMinionsKilled"),
            "neutral_minions_killed": participant.get("neutralMinionsKilled"),
            "neutral_minions_killed_team_jungle": participant.get("neutralMinionsKilledTeamJungle"),
            "neutral_minions_killed_enemy_jungle": participant.get("neutralMinionsKilledEnemyJungle"),

            # Vision and warding stats
            "vision_score": participant.get("visionScore"),
            "wards_placed": participant.get("wardsPlaced"),
            "wards_killed": participant.get("wardsKilled"),
            "vision_wards_bought": participant.get("visionWardsBoughtInGame"),
            "vision_wards_placed": participant.get("visionWardsPlaced"),
            "sight_wards_bought": participant.get("sightWardsBoughtInGame"),

            # Utility stats
            "time_ccing_others": participant.get("timeCCingOthers"),
            "total_time_cc_dealt": participant.get("totalTimeCCDealt"),
            "total_heal": participant.get("totalHeal"),
            "total_units_healed": participant.get("totalUnitsHealed"),
            "total_time_spent_dead": participant.get("totalTimeSpentDead"),
            "largest_killing_spree": participant.get("largestKillingSpree"),
            "largest_multi_kill": participant.get("largestMultiKill"),
            "killing_sprees": participant.get("killingSprees"),
            "unreal_kills": participant.get("unrealKills"),
            "longest_time_spent_living": participant.get("longestTimeSpentLiving"),
            "double_kills": participant.get("doubleKills"),
            "triple_kills": participant.get("tripleKills"),
            "quadra_kills": participant.get("quadraKills"),
            "penta_kills": participant.get("pentaKills"),

            # Summoner spells
            "summoner1_id": participant.get("summoner1Id"),
            "summoner2_id": participant.get("summoner2Id"),

            # Items
            "item0": participant.get("item0"),
            "item1": participant.get("item1"),
            "item2": participant.get("item2"),
            "item3": participant.get("item3"),
            "item4": participant.get("item4"),
            "item5": participant.get("item5"),
            "item6": participant.get("item6"),

            # Additional information
            "first_blood": participant.get("firstBloodKill"),
            "first_blood_assist": participant.get("firstBloodAssist"),
            "first_tower_kill": participant.get("firstTowerKill"),
            "first_tower_assist": participant.get("firstTowerAssist"),
            "first_inhibitor_kill": participant.get("firstInhibitorKill"),
            "first_inhibitor_assist": participant.get("firstInhibitorAssist"),
            "game_ended_in_early_surrender": participant.get("gameEndedInEarlySurrender"),
            "individual_position": participant.get("individualPosition"),
            "team_early_surrendered": participant.get("teamEarlySurrendered"),
            "win": participant.get("win")
        }
        processed_data["players"].append(player_data)

    return processed_data
