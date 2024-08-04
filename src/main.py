# src/main.py

import sys
import os

# Print the current working directory and the sys.path for debugging
print(f"Current working directory: {os.getcwd()}")
print(f"Initial sys.path: {sys.path}")

# Ensure the parent directory of 'src' is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Print the sys.path after modification
print(f"Modified sys.path: {sys.path}")

import pandas as pd
from src.fetch_data import get_match_data
from src.process_data import process_match_data
from src.store_data import store_match_data
from src.analyse_data import calculate_team_averages

def main():
    # Load the Excel file with match details
    excel_path = "data/excel_inputs/input1.xlsx"
    df = pd.read_excel(excel_path, header=None)  # No header in the Excel file

    # Debug: Print first few rows to verify data structure
    print(df.head())

    for index, row in df.iterrows():
        split = row[0]
        division = row[1]
        match_type = row[2]
        blue_team_name = row[3]
        red_team_name = row[4]
        game_id = row[5]
        
        print(f"Processing GameId: {game_id}")
        try:
            # Fetch data
            raw_data = get_match_data(str(game_id))
            if not raw_data:
                print(f"Failed to fetch data for GameId {game_id}")
                continue

            # Process data
            processed_data = process_match_data(raw_data)
            print(f"Processed data for GameId {game_id}")

            # Store data
            store_match_data(processed_data)
            print(f"Stored data for GameId {game_id}")

        except Exception as e:
            print(f"Error processing GameId {game_id}: {e}")

    # Analyse data
    team_averages = calculate_team_averages()
    print("Team Averages:", team_averages)

if __name__ == "__main__":
    main()
