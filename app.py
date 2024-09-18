from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
from datetime import datetime
import locale

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["lol_matches"]

# Fetch the latest version and mappings from DataDragon
def fetch_latest_version_and_data():
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

        # Fetch rune data
        rune_response = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/runesReforged.json')
        rune_data = rune_response.json()

        # Fetch spell data
        spell_response = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/summoner.json')
        spell_data = spell_response.json()

        # Create mappings
        champion_map = {int(champ['key']): champ['id'] for champ in champion_data['data'].values()}
        item_map = {int(item_id): item['image']['full'] for item_id, item in item_data['data'].items()}
        rune_map = {rune['id']: rune['icon'] for path in rune_data for rune in path['slots'][0]['runes']}
        rune_style_map = {style['id']: style['icon'] for style in rune_data}
        spell_map = {int(spell['key']): spell['id'] for spell in spell_data['data'].values()}

        return latest_version, champion_map, item_map, rune_map, rune_style_map, spell_map
    except Exception as e:
        print(f"Error fetching DataDragon data: {e}")
        return "latest", {}, {}, {}, {}, {}

# Load DataDragon assets on server start
latest_version, champion_map, item_map, rune_map, rune_style_map, spell_map = fetch_latest_version_and_data()

# Custom filter to format numbers with commas
@app.template_filter('number_format')
def number_format(value):
    try:
        return locale.format_string("%d", value, grouping=True)
    except (ValueError, TypeError):
        return value

# Custom filter to format dates
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    try:
        # Assuming value is in milliseconds, convert to seconds
        value_in_seconds = value / 1000 if value > 1000000000000 else value
        return datetime.utcfromtimestamp(value_in_seconds).strftime(format)
    except (OSError, ValueError) as e:
        # Handle invalid timestamps gracefully
        return "Invalid Date"

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
    matches = list(db['matches'].find())

    for match in matches:
        game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
        match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if game_start_timestamp else "Date not available"

        resolved_teams = []
        for team_id in match.get('teams', []):
            try:
                team = db['teams'].find_one({"_id": ObjectId(team_id)}) if ObjectId.is_valid(team_id) else db['teams'].find_one({"team_name": team_id})
                resolved_teams.append(team if team else {"team_name": team_id})
            except Exception:
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
            except Exception:
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
            match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if game_start_timestamp else "Date not available"

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

        team['match_history'] = matches

    return render_template('teams_list.html', data=teams)

@app.route('/match_detail/<object_id>')
def match_detail(object_id):
    """Display detailed information about a specific match."""
    match = db['matches'].find_one({"_id": ObjectId(object_id)})

    if not match:
        return "Match not found", 404

    # Add the latest version and mappings to the match data
    match['latestVersion'] = latest_version
    match['championMap'] = champion_map
    match['itemMap'] = item_map
    match['runeMap'] = rune_map
    match['runeStyleMap'] = rune_style_map
    match['spellMap'] = spell_map

    # Game date
    game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
    match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if game_start_timestamp else "Date not available"

    # Resolve team names
    resolved_teams = []
    for team_id in match.get('teams', []):
        try:
            team = db['teams'].find_one({"_id": ObjectId(team_id)}) if ObjectId.is_valid(team_id) else db['teams'].find_one({"team_name": team_id})
            resolved_teams.append(team if team else {"team_name": team_id})
        except:
            resolved_teams.append({"team_name": team_id})
    match['teams'] = resolved_teams

    # Create a mapping of summonerId to player _id
    player_ids = {}
    for player in match.get('data', {}).get('info', {}).get('participants', []):
        player_object = db['players'].find_one({"summonerId": player['summonerId']})
        if player_object:
            player_ids[player['summonerId']] = str(player_object['_id'])

    # Add player_ids to match object
    match['player_ids'] = player_ids

    return render_template('match_detail.html', match_detail=match)


@app.route('/player_detail/<object_id>')
def player_detail(object_id):
    """Display detailed information about a specific player."""
    player = None
    try:
        # Fetch player details using ObjectId
        player = db['players'].find_one({"_id": ObjectId(object_id)})
    except Exception:
        # Fallback if ObjectId isn't valid
        player = db['players'].find_one({"_id": object_id}) or \
                 db['players'].find_one({"summoner_ids": object_id})

    if not player:
        return "Player not found", 404

    # Retrieve the player's current teams
    player['current_teams'] = [
        db['teams'].find_one({"_id": ObjectId(team_id)}) 
        for team_id in player.get('current_teams', []) if ObjectId.is_valid(team_id)
    ]

    # Fetch match history details
    match_ids = player.get('match_history', [])[:10]  # Fetch the latest 10 matches
    matches = []
    win_count = 0
    total_time_spent = 0  # Total time spent in-game (in seconds)

    # Initialize stats_totals
    player['stats_totals'] = {}

    for match_id in match_ids:
        match = db['matches'].find_one({"_id": ObjectId(match_id)})
        if match:
            match['latestVersion'] = latest_version
            match['championMap'] = champion_map

            # Resolve the teams and determine win/loss
            resolved_teams = []
            for team_id in match.get('teams', []):
                resolved_team = db['teams'].find_one(
                    {"_id": ObjectId(team_id)} if ObjectId.is_valid(team_id) else {"team_name": team_id}
                ) or {"team_name": "Unknown Team"}
                resolved_teams.append(resolved_team)
            match['teams'] = resolved_teams

            # Determine which team the player was on
            player_team = None
            player_team_win = False
            game_duration = match.get('data', {}).get('info', {}).get('gameDuration', 0)
            total_time_spent += game_duration  # Add the match duration to the total time spent

            for participant in match['data']['info']['participants']:
                if participant['summonerId'] in player['summoner_ids']:
                    if participant['teamId'] == 100:
                        player_team = match['teams'][0]
                        player_team_win = match['data']['info']['teams'][0]['win']
                    else:
                        player_team = match['teams'][1]
                        player_team_win = match['data']['info']['teams'][1]['win']
                    if player_team_win:
                        win_count += 1  # Increment win count if the player was on the winning team

                    # Aggregate stats for averages
                    for stat_key, stat_value in participant.items():
                        if isinstance(stat_value, (int, float)):
                            player['stats_totals'][stat_key] = player['stats_totals'].get(stat_key, 0) + stat_value

            # Add the timestamp for sorting
            game_start_timestamp = match.get('data', {}).get('game_start_timestamp')
            match['date'] = datetime.utcfromtimestamp(game_start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') if game_start_timestamp else "Date not available"
            match['timestamp'] = game_start_timestamp or 0  # Set to 0 if None, to handle sorting

            match['player_team'] = player_team
            match['player_team_win'] = player_team_win
            matches.append(match)

    # Sort matches by timestamp in ascending order, oldest to newest
    matches.sort(key=lambda x: x['timestamp'] if x['timestamp'] is not None else 0, reverse=False)

    # Convert total time spent to hours, minutes, and seconds format
    total_time_spent_hours = total_time_spent // 3600
    total_time_spent_minutes = (total_time_spent % 3600) // 60
    total_time_spent_seconds = total_time_spent % 60

    formatted_total_time_spent = f"{total_time_spent_hours}h {total_time_spent_minutes}m {total_time_spent_seconds}s"

    return render_template(
        'player_detail.html', 
        player_detail=player, 
        matches=matches, 
        win_count=win_count,
        total_time_spent_in_seconds=total_time_spent,  # Pass total time in seconds
        total_time_spent=formatted_total_time_spent,  # Pass formatted total time
        latestVersion=latest_version, 
        championMap=champion_map
    )


@app.route('/team_detail/<object_id>')
def team_detail(object_id):
    """Display detailed information about a specific team."""
    team = db['teams'].find_one({"_id": ObjectId(object_id)})

    if not team:
        print("Team not found")
        return "Team not found", 404

    # Retrieve current roster
    current_roster = []
    for player_id in team.get('current_roster', []):
        player = db['players'].find_one({'_id': ObjectId(player_id)}) if ObjectId.is_valid(player_id) else db['players'].find_one({'summoner_ids': player_id})
        current_roster.append(player if player else {"summoner_names": ["Unknown Player"]})
    team['current_roster'] = current_roster

    # Fetch the last 10 matches and their details
    match_history_ids = team.get('match_history', [])
    matches = list(db['matches'].find({
        '_id': {
            '$in': [ObjectId(match_id) for match_id in match_history_ids if ObjectId.is_valid(match_id)]
        }
    }))

    # Initialize wins and losses counters
    wins = 0
    losses = 0

    # Debugging output for matches fetched
    print(f"Total matches found: {len(matches)}")

    # Get the team's name for comparison
    current_team_name = team.get('team_name', 'Unknown')

    # Process each match to determine wins and losses
    for match in matches:
        print(f"Processing match: {match.get('_id')}")

        # Extract teams involved in the match
        match_teams = match.get('teams', [])
        print(f"Teams in match: {match_teams}")

        # Ensure the current team is part of this match
        if current_team_name not in match_teams:
            print(f"Current team ({current_team_name}) is NOT in the match.")
            continue

        # Retrieve the winner information based on team ID
        match_info = match.get('data', {}).get('info', {}).get('teams', [])
        if len(match_info) != 2:
            print("Match info does not have exactly two teams.")
            continue
        
        # Map the team names to their respective IDs
        team_100_name = match_teams[0] if match_info[0]['teamId'] == 100 else match_teams[1]
        team_200_name = match_teams[1] if match_info[1]['teamId'] == 200 else match_teams[0]

        print(f"Team 100: {team_100_name}, Team 200: {team_200_name}")

        # Determine if the current team won or lost
        if current_team_name == team_100_name and match_info[0]['win']:
            wins += 1
            print(f"Current team ({current_team_name}) won the match. Total wins: {wins}")
        elif current_team_name == team_200_name and match_info[1]['win']:
            wins += 1
            print(f"Current team ({current_team_name}) won the match. Total wins: {wins}")
        else:
            losses += 1
            print(f"Current team ({current_team_name}) lost the match. Total losses: {losses}")

    # Debug output for final win/loss tally
    print(f"Final Wins: {wins}, Final Losses: {losses}")

    team['match_history'] = matches
    team['wins'] = wins
    team['losses'] = losses

    # Pass `latestVersion` and `championMap` correctly
    return render_template('team_detail.html', team_detail=team, latestVersion=latest_version, championMap=champion_map)


if __name__ == '__main__':
    app.run(debug=True)
