from flask import Flask, request, render_template, g
import sqlite3, os

app = Flask(__name__)
DB = "users.db"
FLAG = os.environ.get("CHALLENGE_FLAG", "FLAG{sql1_1nj3ct10n_byp4ss}")

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'S3cr3tP@ss!', 'admin')")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('guest', 'guest123', 'user')")
        conn.commit()
        conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    result = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        # VULNÉRABLE : concaténation directe, pas de requête paramétrée
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cur.execute(query)
        user = cur.fetchone()
        conn.close()
        if user:
            result = f"Bienvenue {user[1]} (role: {user[3]})"
            if user[3] == "admin":
                result += f" — {FLAG}"
        else:
            result = "Identifiants invalides"
    return render_template("login.html", result=result)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
