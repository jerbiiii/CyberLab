from flask import Flask, request, render_template, send_from_directory
import os, uuid, re, subprocess

app = Flask(__name__)
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FLAG = os.environ.get("CHALLENGE_FLAG", "FLAG{unr3str1ct3d_up10ad_rce_w3bsh3ll}")

ALLOWED_EXT = {".pdf", ".doc", ".docx"}

@app.route("/", methods=["GET", "POST"])
def upload():
    message = None
    if request.method == "POST":
        file = request.files.get("cv")
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext == ".php":
                message = "Extension .php interdite."
            else:
                # VULNÉRABLE : accepte tout sauf .php exact -> .phtml, .php5, .pht passent
                safe_name = str(uuid.uuid4()) + ext
                file.save(os.path.join(UPLOAD_DIR, safe_name))
                message = f"CV reçu : {safe_name}"
    return render_template("upload.html", message=message)

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return "Not found", 404
    # Simule un serveur mal configuré qui exécute les .phtml comme du code serveur
    if filename.endswith((".phtml", ".php5", ".pht")):
        with open(path) as f:
            content = f.read()
        m = re.search(r"<\?cmd\s+(.*?)\?>", content, re.DOTALL)
        if m:
            try:
                output = subprocess.check_output(m.group(1).strip(), shell=True, stderr=subprocess.STDOUT, timeout=5)
                return "<pre>" + output.decode(errors="replace") + "</pre>"
            except subprocess.CalledProcessError as e:
                return "<pre>" + e.output.decode(errors="replace") + "</pre>"
        return "Aucune commande trouvée dans le fichier."
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/flag-location")
def flag_hint():
    return f"Le flag est accessible si tu obtiens une exécution de commande (cat /flag.txt)."

if __name__ == "__main__":
    # Dépose le flag dans un fichier accessible uniquement via RCE
    with open("/flag.txt", "w") as f:
        f.write(FLAG)
    app.run(host="0.0.0.0", port=5005)
