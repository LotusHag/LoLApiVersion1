# tests/test_app.py

import unittest
from app import app

class BasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
    
    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Team Data', response.data)

    def test_add_match_page(self):
        response = self.app.get('/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add New Match', response.data)

if __name__ == "__main__":
    unittest.main()
