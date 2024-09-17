# tests/test_fetch_data.py

import unittest
from src.fetch_data import get_match_data

class TestFetchData(unittest.TestCase):
    def test_get_match_data(self):
        game_id = "7033774635"  # Example GameId
        data = get_match_data(game_id)
        self.assertIsNotNone(data, "Failed to fetch match data")
        self.assertIn("metadata", data, "Metadata missing in fetched data")
        self.assertIn("info", data, "Info missing in fetched data")

if __name__ == "__main__":
    unittest.main()
