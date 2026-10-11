from flask import Flask, request, render_template, redirect
import sqlite3, os, uuid, threading, time, asyncio
from playwright.async_api import async_playwright

app = Flask(__name__)
DB = "avis.db"

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE avis (id INTEGER PRIMARY KEY, auteur TEXT, commentaire TEXT)")
        conn.execute("CREATE TABLE admin_sessions (token TEXT PRIMARY KEY, flag TEXT)")
        admin_token = str(uuid.uuid4())
        conn.execute("INSERT INTO admin_sessions (token, flag) VALUES (?, ?)",
                      (admin_token, "FLAG{st0r3d_xss_c00k13_th3ft}"))
        conn.commit()
        conn.close()
        print(f"[ADMIN] token de session initial : {admin_token}")
        return admin_token

@app.route("/", methods=["GET", "POST"])
def avis():
    if request.method == "POST":
        auteur = request.form.get("auteur", "Anonyme")
        commentaire = request.form.get("commentaire", "")
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO avis (auteur, commentaire) VALUES (?, ?)", (auteur, commentaire))
        conn.commit()
        conn.close()
        return redirect("/")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT auteur, commentaire FROM avis ORDER BY id DESC")
    avis_list = cur.fetchall()
    conn.close()
    return render_template("avis.html", avis_list=avis_list)

@app.route("/admin/cookie", methods=["GET"])
def admin_cookie():
    token = request.args.get("token", "")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT flag FROM admin_sessions WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"flag": row[0]}
    return {"error": "invalid token"}, 403

@app.route("/exfil", methods=["GET"])
def exfil():
    data = request.args.get("data", "")
    with open("exfil.log", "a") as f:
        f.write(data + "\n")
    return "", 204

@app.route("/exfil/log", methods=["GET"])
def exfil_log():
    if not os.path.exists("exfil.log"):
        return "Rien reçu pour le moment."
    with open("exfil.log") as f:
        return "<pre>" + f.read() + "</pre>"

async def visit_page(token):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        context = await browser.new_context()
        await context.add_cookies([{
            "name": "admin_token",
            "value": token,
            "url": "http://localhost:5002"
        }])
        page = await context.new_page()
        try:
            await page.goto("http://localhost:5002/", timeout=5000)
            await page.wait_for_timeout(2000)  # laisse le temps au JS de s'exécuter
        except Exception as e:
            print(f"[BOT] erreur: {e}")
        await browser.close()

def admin_bot(token):
    time.sleep(5)
    while True:
        asyncio.run(visit_page(token))
        time.sleep(15)

if __name__ == "__main__":
    token = init_db()
    if token is None:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT token FROM admin_sessions LIMIT 1")
        token = cur.fetchone()[0]
        conn.close()
    threading.Thread(target=admin_bot, args=(token,), daemon=True).start()
    app.run(host="0.0.0.0", port=5002)
