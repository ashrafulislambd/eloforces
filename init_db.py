import sqlite3

conn = sqlite3.connect("eloforces.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    handle TEXT PRIMARY KEY,
    rating INTEGER DEFAULT 800,
    provisional INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS solved (
    handle TEXT,
    contest_id INTEGER,
    problem_index TEXT,
    PRIMARY KEY (handle, contest_id, problem_index)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS problems (
    contest_id INTEGER,
    problem_index TEXT,
    rating INTEGER,
    PRIMARY KEY (contest_id, problem_index)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    handle TEXT,
    contest_id INTEGER,
    problem_index TEXT,
    verdict TEXT,
    timestamp INTEGER
)
""")

conn.commit()
conn.close()

print("Database initialized successfully!")
