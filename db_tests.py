import unittest
import db_utils

class TestDBUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up database and tables before any tests run."""
        # Assumes create_database doesn't need to be called every time if the db already exists
        # Consider manual management of the test database creation and deletion
        db_utils.rebuild_tables()

    def test_start_session(self):
        """Test starting a new session."""
        session_id = db_utils.start_session()
        self.assertIsNotNone(session_id)

    def test_create_game(self):
        """Test creating a new game."""
        session_id = db_utils.start_session()
        game_id = db_utils.create_game(session_id, 3)
        self.assertIsNotNone(game_id)

    def test_create_player(self):
        """Test creating a new player."""
        player_id = db_utils.create_player("TestPlayer")
        self.assertIsNotNone(player_id)

    def test_add_player_to_game(self):
        """Test adding a player to a game."""
        session_id = db_utils.start_session()
        game_id = db_utils.create_game(session_id)
        player_id = db_utils.create_player("TestPlayer")
        db_utils.add_player_to_game(game_id, player_id)
        # Verify that the player was added to the game
        player_count = db_utils.exec_get_one("SELECT COUNT(*) FROM PlayerGames WHERE GameID = %s", (game_id,))[0]
        self.assertEqual(player_count, 1)

    def test_add_round(self):
        """Test playing a round."""
        # Start a session and create a game
        session_id = db_utils.start_session()
        game_id = db_utils.create_game(session_id, 3)

        # Create players
        player1_id = db_utils.create_player("Player1")
        player2_id = db_utils.create_player("Player2")
        
        # Since your original test assumes winner_id = 1, we'll use player1_id as the winner.
        # However, ensure that player IDs are used correctly in relation to your game logic.
        winner_id = player1_id

        # Play a round
        round_number = 1
        p1_choice = "Rock"
        p2_choice = "Scissors"
        db_utils.add_round(game_id, round_number, p1_choice, p2_choice, winner_id)
        # Verify that the round was added
        round_count = db_utils.exec_get_one("SELECT COUNT(*) FROM Rounds WHERE GameID = %s AND RoundNumber = %s", (game_id, round_number))[0]
        self.assertEqual(round_count, 1)
        # Add more rounds to test the win condition
        round_number = 2
        p1_choice = "Paper"
        p2_choice = "Rock"
        db_utils.add_round(game_id, round_number, p1_choice, p2_choice, winner_id)
        round_number = 3
        p1_choice = "Scissors"
        p2_choice = "Paper"
        db_utils.add_round(game_id, round_number, p1_choice, p2_choice, winner_id)
        # Verify that the game has ended
        game_winner = db_utils.exec_get_one("SELECT WinnerID FROM Games WHERE GameID = %s", (game_id,))[0]
        self.assertEqual(game_winner, winner_id)
        # Make sure the session end time is set
        session_end_time = db_utils.exec_get_one("SELECT EndTime FROM Sessions WHERE SessionID = %s", (session_id,))[0]
        self.assertIsNotNone(session_end_time)

    @classmethod
    def tearDown(cls):
        """Clean up after each test."""
        # Clearing test data from tables; adjust table names as needed
        tables = ["Rounds", "PlayerGames", "Games", "Sessions", "Players"]
        for table in tables:
            db_utils.exec_commit(f"DELETE FROM {table};")

if __name__ == '__main__':
    unittest.main()
