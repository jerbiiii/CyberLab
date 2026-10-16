from flask import Flask, request, jsonify
import jwt, sqlite3, os, datetime, uuid

SECRET = "cafe123"  # secret volontairement faible, présent dans une wordlist courante
app = Flask(__name__)
DB = "orders.db"
FLAG = os.environ.get("CHALLENGE_FLAG", "FLAG{jwt_w34k_s3cr3t_b0l4_ch41n}")

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
        conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT, details TEXT)")

        admin_pass = str(uuid.uuid4())  # mot de passe admin inconnu, non brute-forçable raisonnablement
        conn.execute("INSERT INTO users (id, username, password, role) VALUES (1,'amira','pass123','user')")
        conn.execute("INSERT INTO users (id, username, password, role) VALUES (2,'youssef','azerty','user')")
        conn.execute("INSERT INTO users (id, username, password, role) VALUES (3,'admin',?,'admin')", (admin_pass,))

        conn.execute("INSERT INTO orders (id, user_id, item, details) VALUES (1,1,'Cappuccino','RAS')")
        conn.execute("INSERT INTO orders (id, user_id, item, details) VALUES (2,2,'Croissant','RAS')")
        conn.execute("INSERT INTO orders (id, user_id, item, details) VALUES (?,?,?,?)", (50, 3, "Commande admin", FLAG))
        conn.commit()
        conn.close()
        print(f"[DEBUG] admin password (non récupérable normalement): {admin_pass}")

def make_token(user_id, username, role):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username", "")
    password = data.get("password", "")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, role FROM users WHERE username=? AND password=?", (username, password))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "invalid credentials"}), 401
    token = make_token(row[0], username, row[1])
    return jsonify({"token": token})

@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError as e:
        return jsonify({"error": f"invalid token: {e}"}), 401

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, item, details FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404

    oid, owner_id, item, details = row
    # Autorisation : propriétaire OU role=admin (venant du JWT, jamais revérifié en base)
    if payload["user_id"] != owner_id and payload.get("role") != "admin":
        return jsonify({"error": "access denied"}), 403

    return jsonify({"id": oid, "item": item, "details": details})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5004)
