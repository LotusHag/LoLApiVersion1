# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
from bson.objectid import ObjectId
from src.store_data import get_database
from datetime import datetime

app = Flask(__name__)

def get_db():
    """Get the MongoDB database connection."""
    db = get_database()
    return db

@app.route('/')
def index():
    """Render the front page with navigation buttons."""
    return render_template('index.html')

@app.route('/general_data')
def general_data():
    """Render the General Data page where users can select Matches, Players, or Teams."""
    return render_template('general_data.html')

@app.route('/input_data')
def input_data():
    """Render the Input page to add new data."""
    return render_template('input.html')

@app.route('/data_analysis')
def data_analysis():
    """Render the Data Analysis page for running various analyses."""
    return render_template('data_analysis.html')

@app.route('/general_data/matches')
def list_matches():
    """List all matches."""
    db = get_db()
    matches = list(db['matches'].find())
    for match in matches:
        game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
        if game_start_timestamp:
            match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            match['date'] = "Date not available"

        resolved_teams = []
        for team_id in match.get('teams', []):
            try:
                team = db['teams'].find_one({"_id": ObjectId(team_id)})
                if team:
                    resolved_teams.append(team)
                else:
                    resolved_teams.append({"team_name": team_id})
            except:
                resolved_teams.append({"team_name": team_id})
        match['teams'] = resolved_teams

    return render_template('matches_list.html', data=matches)

@app.route('/general_data/players')
def list_players():
    """List all players."""
    db = get_db()
    players = list(db['players'].find())
    return render_template('players_list.html', data=players)

@app.route('/general_data/teams')
def list_teams():
    """List all teams."""
    db = get_db()
    teams = list(db['teams'].find())
    for team in teams:
        team['current_roster'] = [
            db['players'].find_one({'_id': player_id}, {'summoner_names': 1}) 
            for player_id in team.get('current_roster', [])
        ]
        match_history_ids = team.get('match_history', [])[-10:]
        matches = db['matches'].find({'_id': {'$in': match_history_ids}})
        team['match_history'] = list(matches)

    return render_template('teams_list.html', data=teams)

@app.route('/general_data/<data_type>/<object_id>')
def data_detail(data_type, object_id):
    """Display detailed information about a specific match, player, or team."""
    db = get_db()
    detail = None

    if data_type == 'matches':
        detail = db['matches'].find_one({"_id": ObjectId(object_id)})
        game_start_timestamp = detail.get('data', {}).get('game_start_timestamp')
        if game_start_timestamp:
            detail['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            detail['date'] = "Date not available"

        resolved_teams = []
        for team_id in detail.get('teams', []):
            try:
                team = db['teams'].find_one({"_id": ObjectId(team_id)})
                if team:
                    resolved_teams.append(team)
                else:
                    resolved_teams.append({"team_name": team_id})
            except:
                resolved_teams.append({"team_name": team_id})
        detail['teams'] = resolved_teams

        if 'info' in detail and 'participants' in detail['info']:
            detail['players'] = [
                {
                    "summoner_name": player.get('summonerName'),
                    "team_id": player.get('teamId'),
                    "kda": f"{player.get('kills')}/{player.get('deaths')}/{player.get('assists')}",
                    "damage_dealt": player.get('totalDamageDealtToChampions'),
                    "damage_taken": player.get('totalDamageTaken'),
                    "gold_earned": player.get('goldEarned'),
                    "cs": player.get('totalMinionsKilled'),
                    "items": [player.get(f'item{i}') for i in range(7)],
                    "spells": [player.get(f'summoner{i}Id') for i in range(1, 3)],
                    "champion": player.get('championName')
                }
                for player in detail['info']['participants']
            ]
        else:
            detail['players'] = []

    elif data_type == 'players':
        detail = db['players'].find_one({"_id": ObjectId(object_id)})
        detail['current_teams'] = [db['teams'].find_one({"_id": ObjectId(team_id)}) for team_id in detail.get('current_teams', [])]

    elif data_type == 'teams':
        detail = db['teams'].find_one({"_id": ObjectId(object_id)})

    else:
        return "Invalid data type specified", 400

    return render_template('data_detail.html', detail=detail, data_type=data_type)

@app.route('/fetch_match_details/<match_id>')
def fetch_match_details(match_id):
    """Fetch detailed match data for AJAX requests."""
    db = get_db()
    match = db['matches'].find_one({"_id": ObjectId(match_id)})

    if not match:
        return jsonify({"error": "Match not found"}), 404

    match_details = {
        "match_id": match.get("match_id"),
        "game_duration": match.get("data", {}).get("game_duration"),
        "game_start_timestamp": match.get("data", {}).get("game_start_timestamp"),
        "teams": match.get("data", {}).get("teams", []),
        "players": match.get("data", {}).get("players", [])
    }

    for player in match_details["players"]:
        player["items"] = [player.get(f'item{i}') for i in range(7)]

    return jsonify(match_details)

if __name__ == '__main__':
    app.run(debug=True)
