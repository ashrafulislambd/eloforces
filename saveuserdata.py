import sqlite3

conn = sqlite3.connect("cf_problems.db")
cursor = conn.cursor()

# Create table for users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    handle TEXT PRIMARY KEY,
    virtual_rating INTEGER DEFAULT 1500,
    rating_provisional BOOLEAN DEFAULT 1
)
""")

# Create table for matches
cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    handle TEXT,
    contestId INTEGER,
    problemIndex TEXT,
    problemRating INTEGER,
    startTime INTEGER,
    endTime INTEGER,
    solved BOOLEAN,
    FOREIGN KEY (handle) REFERENCES users(handle)
)
""")

conn.commit()
conn.close()
