import tkinter as tk
from tkinter import messagebox
from math import exp
import threading
import time
import sqlite3
import utils2
import requests

def get_problem_rating(contestId, index):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT rating FROM problems WHERE contestId=? AND \"index\"=?", (contestId, index))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def get_time_from_rating(rating):
    a = 15
    b = 0.0015
    return int(a*exp(b*(rating - 800)))

DB_PATH = "cf_problems.db"
TIME_LIMIT = 60 * 20  # seconds; adjust for different match durations

class CFMatchmakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CF Matchmaking")
        self.geometry("500x450")

        # initialize database
        self.init_db()

        # virtual rating and match state
        self.user_handle = tk.StringVar()
        self.virtual_rating = tk.IntVar(value=0)
        self.current_contest = None
        self.current_index = None
        self.timer_seconds = TIME_LIMIT
        self.timer_running = False

        # UI setup
        tk.Label(self, text="Codeforces Handle:").pack(pady=5)
        entry = tk.Entry(self, textvariable=self.user_handle)
        entry.pack(pady=5)
        entry.bind("<Return>", lambda e: self.load_user_rating())

        tk.Button(self, text="Load Rating", command=self.load_user_rating).pack(pady=2)

        tk.Label(self, text="Virtual Rating:").pack(pady=5)
        tk.Label(self, textvariable=self.virtual_rating, font=(None, 24)).pack(pady=5)

        self.problem_label = tk.Label(self, text="No problem matched yet", wraplength=480)
        self.problem_label.pack(pady=10)

        self.timer_label = tk.Label(self, text=self.format_time(TIME_LIMIT), font=(None, 18))
        self.timer_label.pack(pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        self.match_btn = tk.Button(btn_frame, text="Match Problem", command=self.start_match, state=tk.DISABLED)
        self.match_btn.grid(row=0, column=0, padx=10)
        self.submit_btn = tk.Button(btn_frame, text="Submit", command=self.submit_result, state=tk.DISABLED)
        self.submit_btn.grid(row=0, column=1, padx=10)

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                handle TEXT PRIMARY KEY
            )
        """)
        cur.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cur.fetchall()]
        if 'rating' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN rating INTEGER")
        conn.commit()
        conn.close()

    def load_user_rating(self):
        handle = self.user_handle.get().strip()
        if not handle:
            messagebox.showerror("Error", "Enter a Codeforces handle first.")
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT rating FROM users WHERE handle=?", (handle,))
        row = None
        try:
            row = cur.fetchone()
        except sqlite3.OperationalError:
            messagebox.showerror("DB Error", "The users table is missing the rating column.")
        if row and row[0] is not None:
            self.virtual_rating.set(row[0])
        else:
            self.virtual_rating.set(800)
            cur.execute("INSERT OR REPLACE INTO users(handle, rating) VALUES(?,?)", (handle, 800))
            conn.commit()
        conn.close()
        self.match_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Loaded", f"Virtual rating for {handle}: {self.virtual_rating.get()}")

    def start_match(self):
        handle = self.user_handle.get().strip()
        low = self.virtual_rating.get() - 100
        high = self.virtual_rating.get() + 100
        prob = utils2.get_unsolved_problem_in_range(handle, low, high)
        if prob is None:
            messagebox.showinfo("Info", f"No unsolved problems in range {low}-{high}.")
            return

        self.current_contest, self.current_index = prob
        url = f"https://codeforces.com/problemset/problem/{self.current_contest}/{self.current_index}"
        self.problem_label.config(text=f"Problem: {self.current_contest}{self.current_index}\n{url}")
        self.submit_btn.config(state=tk.NORMAL)
        self.match_btn.config(state=tk.DISABLED)

        rating = get_problem_rating(self.current_contest, self.current_index)

        self.reset_timer(rating)
        if not self.timer_running:
            threading.Thread(target=self.run_timer, daemon=True).start()

    def reset_timer(self, rating):
        self.timer_seconds = get_time_from_rating(rating) * 60
        self.update_timer_label()

    def run_timer(self):
        self.timer_running = True
        while self.timer_running and self.timer_seconds > 0:
            time.sleep(1)
            self.timer_seconds -= 1
            self.update_timer_label()
        if self.timer_running and self.timer_seconds <= 0:
            messagebox.showinfo("Time's up", "Time is over!")
            self.finish_match(False)

    def update_timer_label(self):
        self.timer_label.config(text=self.format_time(self.timer_seconds))

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"Timer: {mins:02d}:{secs:02d}"

    def submit_result(self):
        data = requests.get(f"https://codeforces.com/api/user.status?handle={self.user_handle.get().strip()}").json()
        if data.get('status') != 'OK':
            messagebox.showerror("Error", "Failed to fetch submissions.")
            return
        solved = any(
            sub.get('verdict')=='OK' and
            sub['problem'].get('contestId')==self.current_contest and
            sub['problem'].get('index')==self.current_index
            for sub in data['result']
        )
        self.finish_match(solved)

    def finish_match(self, solved):
        self.timer_running = False
        old = self.virtual_rating.get()
        prob_rating = get_problem_rating(self.current_contest, self.current_index)
        new = utils2.calculate_new_rating(old, prob_rating, solved)
        self.virtual_rating.set(new)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE users SET rating=? WHERE handle=?", (new, self.user_handle.get().strip()))
        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Result", f"You {'solved' if solved else 'did not solve'} the problem.\nNew virtual rating: {new}"
        )
        self.submit_btn.config(state=tk.DISABLED)
        self.match_btn.config(state=tk.NORMAL)
        self.problem_label.config(text="No problem matched yet")

print([(r, get_time_from_rating(r)) for r in range(800, 2400, 100)])

if __name__ == '__main__':
    app = CFMatchmakerApp()
    app.mainloop()
