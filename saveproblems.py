import requests
import sqlite3

# Step 1: Get problem data from Codeforces API
url = "https://codeforces.com/api/problemset.problems"
response = requests.get(url)
data = response.json()

if data['status'] != 'OK':
    raise Exception("Failed to fetch data from Codeforces API")

problems = data['result']['problems']

# Step 2: Set up SQLite DB
conn = sqlite3.connect("cf_problems.db")
cursor = conn.cursor()

# Step 3: Create table (index is a reserved keyword, so we use "index")
cursor.execute("""
CREATE TABLE IF NOT EXISTS problems (
    contestId INTEGER,
    "index" TEXT,
    name TEXT,
    rating INTEGER,
    tags TEXT,
    PRIMARY KEY (contestId, "index")
)
""")

# Step 4: Insert problems
inserted = 0
for problem in problems:
    contestId = problem.get('contestId')
    index = problem.get('index')
    name = problem.get('name')
    rating = problem.get('rating')
    tags = ",".join(problem.get('tags', []))

    try:
        cursor.execute("""
        INSERT OR IGNORE INTO problems (contestId, "index", name, rating, tags)
        VALUES (?, ?, ?, ?, ?)
        """, (contestId, index, name, rating, tags))
        inserted += 1
    except Exception as e:
        print(f"Error inserting problem {contestId}-{index}: {e}")

# Step 5: Commit and close
conn.commit()
conn.close()
print(f"✅ Inserted {inserted} problems into the database.")
