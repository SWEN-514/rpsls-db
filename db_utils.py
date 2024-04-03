import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Connection parameters
conn_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'rpsls-db.ctgqwgm48jhi.us-east-1.rds.amazonaws.com',
    'port': '5432'
}

def connect_to_default():
    """Connect to the default PostgreSQL database."""
    return psycopg2.connect(**conn_params)

def create_database(dbname):
    """Create a new PostgreSQL database."""
    conn = connect_to_default()
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(dbname)
        ))
        print(f"Database '{dbname}' created successfully.")
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()

def rebuild_tables():
    conn = connect_to_db('rpsls_db')
    tables = ["Rounds", "PlayerGames", "Games", "Sessions", "Players"]
    with conn.cursor() as cur:
        # Drop tables in reverse order to avoid foreign key constraints issues
        for table in reversed(tables):
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        conn.commit()

        # Then, execute the SQL script to recreate them
        with open('db_schema.sql', 'r') as file:
            cur.execute(file.read())
        conn.commit()
    print("Tables rebuilt successfully.")

def connect_to_db(dbname):
    """Connect to a specific PostgreSQL database."""
    db_params = conn_params.copy()
    db_params['dbname'] = dbname
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def exec_sql_file(path):
    full_path = os.path.join(os.path.dirname(__file__), path)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return

    conn = connect_to_db('rpsls_db')
    if conn is None:
        return

    try:
        with conn.cursor() as cur, open(full_path, 'r') as file:
            cur.execute(file.read())
        conn.commit()
    except psycopg2.Error as e:
        print(f"An error occurred executing SQL file {path}: {e}")
        conn.rollback()
    finally:
        conn.close()

def exec_get_one(sql, args=None):
    args = args or {}
    conn = connect_to_db('rpsls_db')
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        conn.close()

def exec_get_all(sql, args=None):
    args = args or {}
    conn = connect_to_db('rpsls_db')
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        conn.close()

def exec_commit(sql, args=None):
    args = args or {}
    conn = connect_to_db('rpsls_db')
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
        conn.commit()
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

def exec_return_id(sql, args=None):
    args = args or {}
    conn = connect_to_db('rpsls_db')
    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            conn.commit()
            one = cur.fetchone()
            return one[0] if one else None
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def start_session():
    """
    Starts a new session by inserting a record into the database.
    """
    start_time = datetime.now()
    status = 'InProgress'
    session_id = exec_return_id(
        "INSERT INTO Sessions (StartTime, Status) VALUES (%s, %s) RETURNING SessionID;",
        (start_time, status)
    )
    print(f"Session {session_id} started.")
    return session_id

def create_game(session_id, roundsToWin=None):
    """
    Creates a new game record in the database.

    Parameters:
    session_id (int): The ID of the session the game is part of.
    roundsToWin (int): The number of rounds a player must win to win the game.
    """
    game_id = exec_return_id(
        "INSERT INTO Games (SessionID, RoundsToWin) VALUES (%s, %s) RETURNING GameID;",
        (session_id, roundsToWin)
    )
    print(f"Game {game_id} created.")
    return game_id

def create_player(name, isTemp=False):
    """
    Creates a new player record in the database.
    
    Parameters:
    name (str): The username of the player.
    isTemp (bool): Whether the player is temporary or not.
    """
    player_id = exec_return_id(
        "INSERT INTO Players (Username, IsTemp) VALUES (%s, %s) RETURNING PlayerID;",
        (name, isTemp)
    )
    print(f"Player {player_id} created.")
    return player_id

def add_player_to_game(game_id, player_id):
    """
    Adds a player to a game by inserting a record into a linking table.
    
    Parameters:
    game_id (int): The ID of the game to add the player to.
    player_id (int): The ID of the player to add to the game.
    """
    exec_commit(
        "INSERT INTO PlayerGames (GameID, PlayerID) VALUES (%s, %s);",
        (game_id, player_id)
    )
    print(f"Player {player_id} added to game {game_id}.")


def add_round(game_id, round_number, p1_choice, p2_choice, winner_id):
    """
    Adds a round to a game.

    Parameters:
    game_id (int): The ID of the game the round is played in.
    round_number (int): The number of the round.
    p1_choice (str): The choice of player 1.
    p2_choice (str): The choice of player 2.
    winner_id (int): The ID of the winning player.
    """
    exec_commit(
        """
        INSERT INTO Rounds (GameID, RoundNumber, P1Choice, P2Choice, WinnerID)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (game_id, round_number, p1_choice, p2_choice, winner_id)
    )
    print(f"Round {round_number} played in game {game_id}.")

    # check if the game has been won
    winner = check_win_condition(game_id)
    if winner:
        end_game(game_id, winner)
    

# a function to check if a game meets the win condition of one player winning RoundsToWin rounds
def check_win_condition(game_id):
    """
    Checks if a game has been won by a player.

    Parameters:
    game_id (int): The ID of the game to check.
    """
    roundsToWin = exec_get_one("SELECT RoundsToWin FROM Games WHERE GameID = %s;", (game_id,))[0]
    player_wins = exec_get_all(
        """
        SELECT WinnerID, COUNT(WinnerID) as Wins
        FROM Rounds
        WHERE GameID = %s
        GROUP BY WinnerID
        HAVING COUNT(WinnerID) >= %s;
        """,
        (game_id, roundsToWin)
    )
    if player_wins:
        return player_wins[0][0]
    return None

def end_game(game_id, winner_id=None):
    """
    Ends a game by adding a winner to the game record, and setting the end time in the session record.
    
    Parameters:
    game_id (int): The ID of the game to end.
    winner_id (int): The ID of the winning player. If None, the game is marked as a draw.
    """
    end_time = datetime.now()

    # update the game with the winner
    exec_commit(
        "UPDATE Games SET WinnerID = %s WHERE GameID = %s;",
        (winner_id, game_id)
    )

    # update the session associated with the game with the end time
    session_id = exec_get_one("SELECT SessionID FROM Games WHERE GameID = %s;", (game_id,))[0]
    exec_commit(
        "UPDATE Sessions SET EndTime = %s WHERE SessionID = %s;",
        (end_time, session_id)
    )
    print(f"Game {game_id} ended.")
    return end_time