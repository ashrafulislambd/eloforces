import sqlite3
import random
import requests

def get_problem_in_range(min_rating, max_rating):
    conn = sqlite3.connect("cf_problems.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT contestId, "index" FROM problems
    WHERE rating >= ? AND rating <= ?
    """, (min_rating, max_rating))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None  # no problem found in that range

    contestId, index = random.choice(rows)
    return (contestId, index)

def get_unsolved_problem_in_range(handle, min_rating, max_rating):
    # Step 1: Get user's solved problems
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    resp = requests.get(url).json()
    if resp['status'] != 'OK':
        raise Exception("❌ Failed to fetch user submissions")

    solved = set()
    for sub in resp['result']:
        if sub.get('verdict') == 'OK':
            prob = sub['problem']
            cid = prob.get('contestId')
            idx = prob.get('index')
            if cid and idx:
                solved.add((cid, idx))

    # Step 2: Query DB for problems in rating range
    conn = sqlite3.connect("cf_problems.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT contestId, "index" FROM problems
    WHERE rating >= ? AND rating <= ? AND contestId >= 1471
    """, (min_rating, max_rating))
    all_candidates = cursor.fetchall()
    conn.close()

    # Step 3: Filter out solved ones
    unsolved = [p for p in all_candidates if p not in solved]

    if not unsolved:
        return None

    # Step 4: Pick a random one
    return random.choice(unsolved)  #

def calculate_new_rating(user_rating, problem_rating, win, k=40):
    expected = 1 / (1 + 10 ** ((problem_rating - user_rating) / 400))
    actual = 1 if win else 0
    return round(user_rating + k * (actual - expected))

if __name__ == '__main__':
    print(get_unsolved_problem_in_range('md_ashraful_islam', 1600, 1700))