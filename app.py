from flask import Flask, render_template, request, redirect, url_for, jsonify
from bson.objectid import ObjectId
from src.store_data import get_database
from datetime import datetime
import requests
import locale

app = Flask(__name__)

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, '')

# Custom filter to format numbers with commas
@app.template_filter('number_format')
def number_format(value):
    try:
        return locale.format_string("%d", value, grouping=True)
    except (ValueError, TypeError):
        return value

# Custom filter to format dates
@app.template_filter('date_format')
def date_format(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

# Register the filters with the Flask app
app.jinja_env.filters['number_format'] = number_format
app.jinja_env.filters['date_format'] = date_format

def get_db():
    """Get the MongoDB database connection."""
    db = get_database()
    return db

def fetch_latest_version_and_data():
    """Fetch the latest DataDragon version and champion/item maps."""
    try:
        # Fetch the latest version from DataDragon
        version_response = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
        versions = version_response.json()
        latest_version = versions[0]

        # Fetch champion data
        champion_response = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json')
        champion_data = champion_response.json()

        # Fetch item data
        item_response = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/item.json')
        item_data = item_response.json()

        # Create a mapping of champion IDs to champion names
        champion_map = {int(champ['key']): champ['id'] for champ in champion_data['data'].values()}

        # Create a mapping of item IDs to item image names
        item_map = {int(item_id): item['image']['full'] for item_id, item in item_data['data'].items()}

        return latest_version, champion_map, item_map

    except Exception as e:
        print(f"Error fetching DataDragon data: {e}")
        # Provide fallback values in case of failure
        return "latest", {}, {}

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

    # Fetch the latest version, champion map, and item map
    latest_version, champion_map, item_map = fetch_latest_version_and_data()

    for match in matches:
        game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
        if game_start_timestamp:
            match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            match['date'] = "Date not available"

        resolved_teams = []
        for team_id in match.get('teams', []):
            try:
                team = db['teams'].find_one({"_id": ObjectId(team_id)}) if ObjectId.is_valid(team_id) else db['teams'].find_one({"team_name": team_id})
                if team:
                    resolved_teams.append(team)
                else:
                    resolved_teams.append({"team_name": team_id})
            except Exception as e:
                resolved_teams.append({"team_name": team_id})
        match['teams'] = resolved_teams

        # Ensure participant data includes player ObjectId
        for participant in match['data']['info']['participants']:
            player = db['players'].find_one({"summoner_ids": participant["summonerId"]})
            if player:
                participant['_id'] = player['_id']  # Assign ObjectId to the participant

    return render_template('matches_list.html', data=matches, latestVersion=latest_version, championMap=champion_map, itemMap=item_map)

@app.route('/general_data/players')
def list_players():
    """List all players."""
    db = get_db()
    players = list(db['players'].find())
    for player in players:
        player['current_teams'] = [
            db['teams'].find_one({'_id': ObjectId(team_id)}) 
            for team_id in player.get('current_teams', [])
        ]
    return render_template('players_list.html', data=players)

@app.route('/general_data/teams')
def list_teams():
    """List all teams."""
    db = get_db()
    teams = list(db['teams'].find())

    for team in teams:
        current_roster = []
        for player_id in team.get('current_roster', []):
            try:
                if ObjectId.is_valid(player_id):
                    player = db['players'].find_one({'_id': ObjectId(player_id)})
                else:
                    player = db['players'].find_one({'summoner_ids': player_id})

                if player:
                    current_roster.append(player)
                else:
                    current_roster.append({"summoner_names": ["Unknown Player"]})
            except Exception as e:
                current_roster.append({"summoner_names": ["Unknown Player"]})

        team['current_roster'] = current_roster

        match_history_ids = team.get('match_history', [])[-10:]
        matches = list(db['matches'].find({
            '_id': {
                '$in': [ObjectId(match_id) for match_id in match_history_ids if ObjectId.is_valid(match_id)]
            }
        }))
        for match in matches:
            game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
            if game_start_timestamp:
                match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                match['date'] = "Date not available"

            resolved_teams = []
            for team_id in match.get('teams', []):
                try:
                    resolved_team = db['teams'].find_one(
                        {"_id": ObjectId(team_id)} if ObjectId.is_valid(team_id) else {"team_name": team_id}
                    )
                    resolved_teams.append(resolved_team if resolved_team else {"team_name": team_id})
                except:
                    resolved_teams.append({"team_name": team_id})
            match['teams'] = resolved_teams

            match_teams_data = match.get('data', {}).get('teams', [])
            if match_teams_data:
                match['teams'][0]['bans'] = match_teams_data[0].get('bans', [])
                match['teams'][1]['bans'] = match_teams_data[1].get('bans', [])

        team['match_history'] = matches

    return render_template('teams_list.html', data=teams)

@app.route('/match_detail/<object_id>')
def match_detail(object_id):
    """Display detailed information about a specific match."""
    db = get_db()
    match = db['matches'].find_one({"_id": ObjectId(object_id)})

    if not match:
        return "Match not found", 404

    # Fetch the game start timestamp and format it, if available
    game_start_timestamp = match.get('data', {}).get('info', {}).get('gameStartTimestamp')
    match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if game_start_timestamp else "Date not available"

    # Resolve teams and ensure that team objects are correctly retrieved
    resolved_teams = []
    for team_id in match.get('teams', []):
        try:
            team = db['teams'].find_one({"_id": ObjectId(team_id)}) if ObjectId.is_valid(team_id) else db['teams'].find_one({"team_name": team_id})
            resolved_teams.append(team if team else {"team_name": team_id})
        except:
            resolved_teams.append({"team_name": team_id})
    match['teams'] = resolved_teams

    # Ensure participant data includes player ObjectId and handle potential missing data
    match['players'] = []
    for participant in match.get('data', {}).get('info', {}).get('participants', []):
        player = db['players'].find_one({"summoner_ids": participant.get("summonerId")})
        participant_data = {
            "_id": player['_id'] if player else None,
            "summonerName": participant.get('summonerName', 'Unknown'),
            "championName": participant.get('championName', 'Unknown'),
            "kills": participant.get('kills', 0),
            "deaths": participant.get('deaths', 0),
            "assists": participant.get('assists', 0),
            "totalDamageDealtToChampions": participant.get('totalDamageDealtToChampions', 0),
            "goldEarned": participant.get('goldEarned', 0),
            "visionScore": participant.get('visionScore', 0),
            "items": [participant.get(f'item{i}', None) for i in range(7)]
        }
        match['players'].append(participant_data)

    return render_template('match_detail.html', match_detail=match)

@app.route('/player_detail/<object_id>')
def player_detail(object_id):
    """Display detailed information about a specific player."""
    db = get_db()

    # Try to fetch the player by ObjectId first, then fallback to other potential fields.
    player = None
    try:
        # Attempt to fetch using ObjectId
        player = db['players'].find_one({"_id": ObjectId(object_id)})
    except Exception:
        # Fallback searches using other identifiers
        player = db['players'].find_one({"_id": object_id}) or db['players'].find_one({"summoner_ids": object_id}) or db['players'].find_one({"custom_id": object_id})

    if not player:
        return "Player not found", 404

    # Retrieve the current teams of the player
    player['current_teams'] = [db['teams'].find_one({"_id": ObjectId(team_id)}) for team_id in player.get('current_teams', []) if ObjectId.is_valid(team_id)]

    return render_template('player_detail.html', player_detail=player)

@app.route('/team_detail/<object_id>')
def team_detail(object_id):
    """Display detailed information about a specific team."""
    db = get_db()
    team = db['teams'].find_one({"_id": ObjectId(object_id)})

    if not team:
        return "Team not found", 404

    current_roster = []
    for player_id in team.get('current_roster', []):
        player = db['players'].find_one({'_id': ObjectId(player_id)}) if ObjectId.is_valid(player_id) else db['players'].find_one({'summoner_ids': player_id})
        current_roster.append(player if player else {"summoner_names": ["Unknown Player"]})
    team['current_roster'] = current_roster

    match_history_ids = team.get('match_history', [])[-10:]
    matches = list(db['matches'].find({'_id': {'$in': [ObjectId(match_id) for match_id in match_history_ids if ObjectId.is_valid(match_id)]}}))
    for match in matches:
        game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
        match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if game_start_timestamp else "Date not available"

        resolved_teams = []
        for team_id in match.get('teams', []):
            resolved_team = db['teams'].find_one(
                {"_id": ObjectId(team_id)} if ObjectId.is_valid(team_id) else {"team_name": team_id}
            )
            resolved_teams.append(resolved_team if resolved_team else {"team_name": team_id})
        match['teams'] = resolved_teams

        match_teams_data = match.get('data', {}).get('teams', [])
        if match_teams_data:
            match['teams'][0]['bans'] = match_teams_data[0].get('bans', [])
            match['teams'][1]['bans'] = match_teams_data[1].get('bans', [])

    team['match_history'] = matches

    return render_template('team_detail.html', team_detail=team)

if __name__ == '__main__':
    app.run(debug=True)
