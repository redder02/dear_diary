from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import bcrypt
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this")

DB = "diary.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user["password"].encode()):
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.hashpw(
            request.form["password"].encode(),
            bcrypt.gensalt()
        ).decode()

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except:
            return "Username already exists"

        conn.close()
        return redirect("/")

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/")

    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM entries WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("dashboard.html", entries=entries)

@app.route("/new", methods=["GET", "POST"])
def new_entry():
    if not session.get("user_id"):
        return redirect("/")

    if request.method == "POST":
        content = request.form["content"]

        conn = get_db()
        conn.execute(
            "INSERT INTO entries (user_id, content, created_at) VALUES (?, ?, ?)",
            (session["user_id"], content, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("new.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
