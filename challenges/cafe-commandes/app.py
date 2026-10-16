from flask import Flask, request, render_template, redirect, make_response
import sqlite3, os, uuid

app = Flask(__name__)
DB = "commandes.db"
FLAG = os.environ.get("CHALLENGE_FLAG", "FLAG{1d0r_br0k3n_4cc3ss_c0ntr0l}")

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, session_token TEXT)")
        conn.execute("CREATE TABLE commandes (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT, details TEXT)")

        users = [
            (1, "amira", "pass123"),
            (2, "youssef", "azerty"),
            (3, "admin", "FlagOwner2026"),
        ]
        for uid, uname, pwd in users:
            token = str(uuid.uuid4())
            conn.execute("INSERT INTO users (id, username, password, session_token) VALUES (?, ?, ?, ?)",
                         (uid, uname, pwd, token))

        commandes = [
            (1, 1, "Cappuccino", "Commande normale, rien de spécial."),
            (2, 2, "Croissant x2", "Paiement par carte, reçu envoyé par email."),
            (3, 3, "Thé vert", f"Note interne admin : {FLAG}"),
        ]
        conn.executemany("INSERT INTO commandes (id, user_id, item, details) VALUES (?, ?, ?, ?)", commandes)
        conn.commit()
        conn.close()

def get_user_by_token(token):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE session_token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT id, session_token FROM users WHERE username = ? AND password = ?", (username, password))
        row = cur.fetchone()
        conn.close()
        if row:
            resp = make_response(redirect("/mes-commandes"))
            resp.set_cookie("session_token", row[1])
            return resp
        error = "Identifiants invalides"
    return render_template("login.html", error=error)

@app.route("/mes-commandes")
def mes_commandes():
    token = request.cookies.get("session_token", "")
    user = get_user_by_token(token)
    if not user:
        return redirect("/login")
    user_id, username = user
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, item FROM commandes WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    links = "".join(f'<li><a href="/commande/{cid}">{item}</a></li>' for cid, item in rows)
    return f"<h2>Bonjour {username}</h2><p>Vos commandes :</p><ul>{links}</ul>"

@app.route("/commande/<int:commande_id>")
def commande(commande_id):
    token = request.cookies.get("session_token", "")
    user = get_user_by_token(token)
    if not user:
        return redirect("/login")
    # VULNÉRABLE : pas de vérification que commande.user_id == user.id -> IDOR
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT item, details FROM commandes WHERE id = ?", (commande_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return "Commande introuvable", 404
    return render_template("commande.html", item=row[0], details=row[1], commande_id=commande_id)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5003)
