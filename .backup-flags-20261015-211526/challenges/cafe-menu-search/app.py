from flask import Flask, request, render_template
import sqlite3, os, re

app = Flask(__name__)
DB = "cafe.db"

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price TEXT, category TEXT)")
        conn.execute("CREATE TABLE staff (id INTEGER PRIMARY KEY, username TEXT, secret TEXT)")
        products = [
            ("Espresso", "2.5", "Café"),
            ("Cappuccino", "3.5", "Café"),
            ("Croissant", "2.0", "Pâtisserie"),
            ("Thé vert", "2.0", "Boisson"),
        ]
        conn.executemany("INSERT INTO products (name, price, category) VALUES (?, ?, ?)", products)
        conn.execute("INSERT INTO staff (username, secret) VALUES ('manager', 'FLAG{un10n_b4s3d_3xf1ltr4t10n}')")
        conn.commit()
        conn.close()

# Filtre basique (WAF-lite) à contourner : bloque les mots-clés évidents en minuscule/majuscule simple
BLACKLIST = ["union select", "UNION SELECT", "drop table", "DROP TABLE"]

def is_blocked(payload):
    low = payload.lower()
    return any(bad.lower() in low for bad in BLACKLIST)

@app.route("/", methods=["GET"])
def search():
    results = None
    error = None
    q = request.args.get("q", "")
    if q:
        if is_blocked(q):
            error = "Requête bloquée par le filtre de sécurité."
        else:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            # VULNÉRABLE : concaténation directe dans une requête multi-colonnes (3 colonnes -> exploitable en UNION)
            query = f"SELECT name, price, category FROM products WHERE name LIKE '%{q}%'"
            try:
                cur.execute(query)
                results = cur.fetchall()
            except Exception as e:
                error = str(e)
            conn.close()
    return render_template("search.html", results=results, error=error, q=q)

@app.route("/check", methods=["GET"])
def check():
    # Endpoint volontairement vulnérable au blind boolean-based (pas de UNION filtré ici)
    name = request.args.get("name", "")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    query = f"SELECT 1 FROM products WHERE name = '{name}'"
    try:
        cur.execute(query)
        found = cur.fetchone() is not None
    except Exception:
        found = False
    conn.close()
    return {"exists": found}

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)
