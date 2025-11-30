import sqlite3
import requests
import time

conn = sqlite3.connect("cf_problems.db")
cursor = conn.cursor()

def update_user(handle):
    cursor.execute("SELECT * FROM users WHERE handle = ?", (handle,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (handle, rating, provisional) VALUES (?, ?, ?)", (handle, 800, 1))
        conn.commit()

def get_user_rating(handle):
    cursor.execute("SELECT rating FROM users WHERE handle = ?", (handle,))
    result = cursor.fetchone()
    return result[0] if result else 800

def update_virtual_rating(handle, problem_rating, solved):
    current_rating = get_user_rating(handle)
    K = 40 if is_provisional(handle) else 20
    expected_score = 1 / (1 + 10 ** ((problem_rating - current_rating) / 400))
    actual_score = 1 if solved else 0
    new_rating = round(current_rating + K * (actual_score - expected_score))

    cursor.execute("UPDATE users SET rating = ? WHERE handle = ?", (new_rating, handle))
    conn.commit()

def is_provisional(handle):
    cursor.execute("SELECT provisional FROM users WHERE handle = ?", (handle,))
    result = cursor.fetchone()
    return result[0] == 1 if result else True

def mark_problem_solved(handle, contest_id, index):
    cursor.execute("INSERT INTO solved (handle, contest_id, problem_index) VALUES (?, ?, ?)", (handle, contest_id, index))
    conn.commit()

def save_submission(handle, contest_id, index, verdict):
    timestamp = int(time.time())
    cursor.execute("INSERT INTO matches (handle, contest_id, problem_index, verdict, timestamp) VALUES (?, ?, ?, ?, ?)", (handle, contest_id, index, verdict, timestamp))
    conn.commit()

def get_unsolved_problem(handle, min_rating, max_rating):
    cursor.execute("""
        SELECT contest_id, problem_index FROM problems
        WHERE rating BETWEEN ? AND ?
        AND (contest_id, problem_index) NOT IN (
            SELECT contest_id, problem_index FROM solved WHERE handle = ?
        )
        ORDER BY RANDOM() LIMIT 1
    """, (min_rating, max_rating, handle))
    return cursor.fetchone()

def check_submission(handle, contest_id, index, start_time):
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=20"
    try:
        resp = requests.get(url).json()
        if resp["status"] != "OK":
            return False
        for submission in resp["result"]:
            if submission["problem"].get("contestId") == contest_id and \
               submission["problem"].get("index") == index and \
               submission["creationTimeSeconds"] >= start_time and \
               submission.get("verdict") == "OK":
                return True
    except Exception as e:
        print("Submission check error:", e)
    return False
