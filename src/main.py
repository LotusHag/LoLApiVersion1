# src/main.py

import sys
import os
import pandas as pd

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch_data import get_match_data
from src.process_data import process_match_data
from src.store_data import get_database, store_match_data

def main():
    # Load the Excel file with match details
    excel_path = "data/excel_inputs/input1.xlsx"
    df = pd.read_excel(excel_path, header=None)  # No header in the Excel file

    # Debug: Print first few rows to verify data structure
    print(df.head())

    db = get_database()

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
            store_match_data(db, processed_data, division, split, match_type, blue_team_name, red_team_name)
            print(f"Stored data for GameId {game_id}")

        except Exception as e:
            print(f"Error processing GameId {game_id}: {e}")

    print("Processing complete.")

if __name__ == "__main__":
    main()
