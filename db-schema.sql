CREATE TABLE Players (
    PlayerID SERIAL PRIMARY KEY,
    Username VARCHAR(255),
    IsTemp BOOLEAN
);

CREATE TABLE Sessions (
    SessionID SERIAL PRIMARY KEY,
    StartTime TIMESTAMP,
    EndTime TIMESTAMP,
    Status VARCHAR(50)
);

CREATE TABLE Games (
    GameID SERIAL PRIMARY KEY,
    SessionID INT REFERENCES Sessions(SessionID),
    StartTime TIMESTAMP,
    EndTime TIMESTAMP,
    WinnerID INT REFERENCES Players(PlayerID)
);

CREATE TABLE PlayerGames (
    PlayerGameID SERIAL PRIMARY KEY,
    PlayerID INT REFERENCES Players(PlayerID),
    GameID INT REFERENCES Games(GameID)
);

CREATE TABLE Rounds (
    RoundID SERIAL PRIMARY KEY,
    GameID INT REFERENCES Games(GameID),
    RoundNumber INT,
    P1Choice VARCHAR(50),
    P2Choice VARCHAR(50),
    WinnerID INT REFERENCES Players(PlayerID)
);