from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from groq import Groq

import sqlite3
import os
import json
import random
from datetime import date


# =========================
# SETUP
# =========================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "student-life-secret-key"
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

api_key = os.getenv("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)
else:
    client = None

DATABASE = "student_life.db"


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            quiz_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# USER
# =========================

class User(UserMixin):

    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email


@login_manager.user_loader
def load_user(user_id):

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    if user:
        return User(
            user["id"],
            user["name"],
            user["email"]
        )

    return None


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill all fields.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash(
                "Password must contain at least 6 characters.",
                "error"
            )
            return redirect(url_for("register"))

        conn = get_db()

        existing = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing:

            conn.close()

            flash(
                "Email already registered.",
                "error"
            )

            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn.execute(
            """
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                hashed_password,
                str(date.today())
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Account created successfully! Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            user_obj = User(
                user["id"],
                user["name"],
                user["email"]
            )

            login_user(user_obj)

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("home"))


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db()

    results = conn.execute(
        """
        SELECT * FROM quiz_results
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (current_user.id,)
    ).fetchall()

    conn.close()

    total_quizzes = len(results)

    total_questions = sum(
        result["total"]
        for result in results
    )

    total_correct = sum(
        result["score"]
        for result in results
    )

    if total_questions > 0:

        accuracy = round(
            (total_correct / total_questions) * 100,
            1
        )

    else:

        accuracy = 0

    best_score = 0

    if results:

        best_score = max(
            result["percentage"]
            for result in results
        )

    return render_template(
        "dashboard.html",
        results=results,
        total_quizzes=total_quizzes,
        total_questions=total_questions,
        total_correct=total_correct,
        accuracy=accuracy,
        best_score=best_score
    )


# =========================
# CGPA
# =========================

@app.route("/cgpa", methods=["GET", "POST"])
@login_required
def cgpa():

    result = None

    if request.method == "POST":

        mode = request.form.get("mode")

        try:

            value = float(
                request.form.get("value")
            )

            if mode == "marks":

                percentage = value

                cgpa_value = percentage / 10

                result = {
                    "title": "CGPA",
                    "value": round(cgpa_value, 2),
                    "extra": f"{percentage}%"
                }

            else:

                cgpa_value = value

                percentage = cgpa_value * 10

                result = {
                    "title": "Percentage",
                    "value": round(percentage, 2),
                    "extra": f"CGPA: {cgpa_value}"
                }

        except:

            flash(
                "Please enter a valid number.",
                "error"
            )

    return render_template(
        "cgpa.html",
        result=result
    )


# =========================
# QUIZ PAGE
# =========================

@app.route("/quiz")
@login_required
def quiz():

    return render_template("quiz.html")


# =========================
# AI QUIZ
# =========================

@app.route("/generate_quiz", methods=["POST"])
@login_required
def generate_quiz():

    if not client:

        return jsonify({
            "success": False,
            "message": "Groq API key not found."
        })

    data = request.get_json()

    topic = data.get(
        "topic",
        ""
    ).strip()

    difficulty = data.get(
        "difficulty",
        "Easy"
    )

    try:

        number = int(
            data.get(
                "number",
                5
            )
        )

    except:

        number = 5

    if not topic:

        return jsonify({
            "success": False,
            "message": "Please enter a topic."
        })

    number = max(
        3,
        min(number, 10)
    )

    prompt = f"""
Create {number} multiple choice questions about:

{topic}

Difficulty:
{difficulty}

Return ONLY valid JSON.

Format:

[
  {{
    "question": "Question here",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "Option A",
    "explanation": "Simple explanation"
  }}
]

Rules:

- Exactly {number} questions
- Exactly 4 options
- Only one correct answer
- Keep questions educational
- Do not use markdown
- Return JSON only
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        text = response.choices[0].message.content.strip()

        if text.startswith("```"):

            text = text.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            ).strip()

        questions = json.loads(text)

        session["quiz_topic"] = topic

        return jsonify({
            "success": True,
            "questions": questions
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        })


# =========================
# SAVE QUIZ
# =========================

@app.route("/save_quiz", methods=["POST"])
@login_required
def save_quiz():

    data = request.get_json()

    topic = data.get(
        "topic",
        "General"
    )

    score = int(
        data.get(
            "score",
            0
        )
    )

    total = int(
        data.get(
            "total",
            0
        )
    )

    if total > 0:

        percentage = round(
            (score / total) * 100,
            1
        )

    else:

        percentage = 0

    conn = get_db()

    conn.execute(
        """
        INSERT INTO quiz_results
        (user_id, topic, score, total, percentage, quiz_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            current_user.id,
            topic,
            score,
            total,
            percentage,
            str(date.today())
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# =========================
# GAME
# =========================

@app.route("/game")
@login_required
def game():

    if "game_number" not in session:

        session["game_number"] = random.randint(
            1,
            20
        )

    return render_template("game.html")


@app.route("/game/guess", methods=["POST"])
@login_required
def game_guess():

    data = request.get_json()

    try:

        guess = int(
            data.get("guess")
        )

    except:

        return jsonify({
            "message": "Enter a number."
        })

    number = session.get(
        "game_number"
    )

    if not number:

        number = random.randint(
            1,
            20
        )

        session["game_number"] = number

    if guess == number:

        message = "🎉 Correct! You guessed it!"

        session["game_number"] = random.randint(
            1,
            20
        )

    elif guess < number:

        message = "⬆️ Try a higher number!"

    else:

        message = "⬇️ Try a lower number!"

    return jsonify({
        "message": message
    })


# =========================
# RUN
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )