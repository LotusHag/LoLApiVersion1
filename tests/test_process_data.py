# tests/test_process_data.py

import unittest
from src.process_data import process_match_data

class TestProcessData(unittest.TestCase):
    def test_process_match_data(self):
        raw_data = {
            "metadata": {"matchId": "EUW1_7033774635"},
            "info": {
                "gameDuration": 1234,
                "gameStartTimestamp": 1610000000000,
                "participants": [
                    {
                        "summonerName": "Player1",
                        "championId": 1,
                        "kills": 10,
                        "deaths": 2,
                        "assists": 5,
                        "totalDamageDealt": 20000,
                        "goldEarned": 15000,
                        "teamId": 100,
                        "individualPosition": "MID"
                    }
                ],
                "teams": [
                    {
                        "teamId": 100,
                        "win": True,
                        "objectives": {"baron": {"kills": 1}, "tower": {"kills": 5}},
                        "bans": [{"championId": 10}]
                    }
                ]
            }
        }
        processed_data = process_match_data(raw_data)
        self.assertEqual(processed_data["match_id"], "EUW1_7033774635")
        self.assertEqual(processed_data["game_duration"], 1234)
        self.assertEqual(len(processed_data["players"]), 1)
        self.assertEqual(len(processed_data["teams"]), 1)

if __name__ == "__main__":
    unittest.main()
