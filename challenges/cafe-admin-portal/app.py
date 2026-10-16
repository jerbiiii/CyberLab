from flask import Flask, request, render_template, redirect, make_response
import sqlite3, os, uuid, smtplib, threading, time, asyncio
from email.mime.text import MIMEText
from playwright.async_api import async_playwright

app = Flask(__name__)
DB = "portal.db"
FLAG = os.environ.get("CHALLENGE_FLAG", "FLAG{ph1sh1ng_c10n3_2fa_byp4ss_v14_m4ilh0g}")

MAIL_HOST = "mailhog"
MAIL_PORT = 1025
EMPLOYEE_EMAIL = "fatma@cafesaffran.local"
EMPLOYEE_USER = "fatma"
EMPLOYEE_PASS = "CoffeeLove2026!"

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT, email TEXT)")
        conn.execute("CREATE TABLE tokens (token TEXT PRIMARY KEY, username TEXT, used INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE annonces (id INTEGER PRIMARY KEY, titre TEXT, url TEXT)")
        conn.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                      (EMPLOYEE_USER, EMPLOYEE_PASS, EMPLOYEE_EMAIL))
        conn.commit()
        conn.close()

def send_magic_link(username, email):
    token = str(uuid.uuid4())
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO tokens (token, username) VALUES (?, ?)", (token, username))
    conn.commit()
    conn.close()
    link = f"http://cafe_admin_portal:5007/verify/{token}"
    body = f"""Bonjour,

Une tentative de connexion a ete detectee sur votre compte Cafe Saffran Admin.
Cliquez sur ce lien pour confirmer votre identite et terminer la connexion :

{link}

Si vous n'etes pas a l'origine de cette tentative, ignorez cet email.

-- Cafe Saffran Security Team
"""
    msg = MIMEText(body)
    msg["Subject"] = "Cafe Saffran - Confirmation de connexion"
    msg["From"] = "security@cafesaffran.local"
    msg["To"] = email
    with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as s:
        s.sendmail(msg["From"], [email], msg.as_string())

@app.route("/")
def index():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT email FROM users WHERE username=? AND password=?", (username, password))
        row = cur.fetchone()
        conn.close()
        if row:
            send_magic_link(username, row[0])
            return render_template("check_email.html", email=row[0])
        error = "Identifiants invalides"
    return render_template("login.html", error=error)

@app.route("/verify/<token>")
def verify(token):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username, used FROM tokens WHERE token=?", (token,))
    row = cur.fetchone()
    if not row or row[1] == 1:
        conn.close()
        return "Lien invalide ou deja utilise", 403
    username = row[0]
    conn.execute("UPDATE tokens SET used=1 WHERE token=?", (token,))
    conn.commit()
    conn.close()
    resp = make_response(redirect("/admin/dashboard"))
    resp.set_cookie("session_user", username)
    return resp

@app.route("/admin/dashboard")
def dashboard():
    user = request.cookies.get("session_user")
    if user != EMPLOYEE_USER:
        return redirect("/login")
    return render_template("dashboard.html", flag=FLAG)

@app.route("/annonces", methods=["GET", "POST"])
def annonces():
    conn = sqlite3.connect(DB)
    if request.method == "POST":
        titre = request.form.get("titre", "Annonce")
        url = request.form.get("url", "")
        conn.execute("INSERT INTO annonces (titre, url) VALUES (?, ?)", (titre, url))
        conn.commit()
    cur = conn.cursor()
    cur.execute("SELECT titre, url FROM annonces ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("annonces.html", annonces=rows)

async def visit_latest_announcement():
    print("[BOT] cycle démarré", flush=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT url FROM annonces ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        print('[BOT] aucune annonce trouvée', flush=True)
        return
    url = row[0]
    print(f"[BOT] visite de : {url}", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=5000)
            print("[BOT] page chargée", flush=True)
            has_form = await page.query_selector("input[name='username']") and await page.query_selector("input[name='password']")
            print(f"[BOT] formulaire détecté : {bool(has_form)}", flush=True)
            if has_form:
                await page.fill("input[name='username']", EMPLOYEE_USER)
                await page.fill("input[name='password']", EMPLOYEE_PASS)
                await page.click("button[type='submit'], input[type='submit']")
                await page.wait_for_timeout(1500)
                print("[BOT] formulaire soumis", flush=True)
        except Exception as e:
            print(f"[BOT] erreur : {e}")
        await browser.close()

def employee_bot():
    time.sleep(10)
    while True:
        try:
            asyncio.run(visit_latest_announcement())
        except Exception as e:
            print(f"[BOT] erreur generale : {e}")
        time.sleep(20)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=employee_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=5007)
