# app.py

from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/general_data/<data_type>')
def list_data(data_type):
    """List all matches, players, or teams based on the data_type selected."""
    db = get_db()
    data = []
    
    if data_type == 'matches':
        data = list(db['matches'].find())
        for match in data:
            # Check if 'info' key exists and handle date conversion
            if 'info' in match and 'gameStartTimestamp' in match['info']:
                match['date'] = datetime.utcfromtimestamp(match['info']['gameStartTimestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                match['date'] = "Date not available"

            # Resolve team names or use direct identifiers
            resolved_teams = []
            for team_id in match['teams']:
                try:
                    team = db['teams'].find_one({"_id": ObjectId(team_id)})
                    if team:
                        resolved_teams.append(team)
                    else:
                        resolved_teams.append({"team_name": team_id})  # Assume it's a direct team name
                except:
                    resolved_teams.append({"team_name": team_id})  # Assume it's a direct team name
            match['teams'] = resolved_teams

    elif data_type == 'players':
        data = list(db['players'].find())
    elif data_type == 'teams':
        data = list(db['teams'].find())
    else:
        return "Invalid data type specified", 400
    
    return render_template('data_list.html', data=data, data_type=data_type)

@app.route('/general_data/<data_type>/<object_id>')
def data_detail(data_type, object_id):
    """Display detailed information about a specific match, player, or team."""
    db = get_db()
    detail = None

    if data_type == 'matches':
        detail = db['matches'].find_one({"_id": ObjectId(object_id)})
        # Check if 'info' key exists and handle date conversion
        if 'info' in detail and 'gameStartTimestamp' in detail['info']:
            detail['date'] = datetime.utcfromtimestamp(detail['info']['gameStartTimestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            detail['date'] = "Date not available"
        
        # Resolve team names or use direct identifiers
        resolved_teams = []
        for team_id in detail['teams']:
            try:
                team = db['teams'].find_one({"_id": ObjectId(team_id)})
                if team:
                    resolved_teams.append(team)
                else:
                    resolved_teams.append({"team_name": team_id})  # Assume it's a direct team name
            except:
                resolved_teams.append({"team_name": team_id})  # Assume it's a direct team name
        detail['teams'] = resolved_teams
        
        # Check if 'info' and 'participants' exist before accessing
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
                    "items": [player.get(f'item{i}') for i in range(7)],  # Assumes 7 item slots
                    "spells": [player.get(f'summoner{i}Id') for i in range(1, 3)],  # Assumes 2 summoner spells
                    "champion": player.get('championName')
                }
                for player in detail['info']['participants']
            ]
        else:
            detail['players'] = []  # Default to an empty list if no participants data
        
    elif data_type == 'players':
        detail = db['players'].find_one({"_id": ObjectId(object_id)})
        # Resolve team names
        detail['current_teams'] = [db['teams'].find_one({"_id": ObjectId(team_id)}) for team_id in detail['current_teams']]
    elif data_type == 'teams':
        detail = db['teams'].find_one({"_id": ObjectId(object_id)})
    else:
        return "Invalid data type specified", 400

    return render_template('data_detail.html', detail=detail, data_type=data_type)

if __name__ == '__main__':
    app.run(debug=True)
