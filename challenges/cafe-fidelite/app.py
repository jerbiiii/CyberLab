from flask import Flask, request, render_template, render_template_string
import os, re

app = Flask(__name__)

# "WAF" multi-couches, volontairement incomplet — bloque les payloads évidents
# mais pas les techniques de contournement avancées (concaténation, attributs
# alternatifs, filtres Jinja détournés, accès via des objets globaux non bloqués)
BLACKLIST = [
    "__import__", "os.system", "subprocess", "popen",
    "config", "self", "request.application",
]

def is_blocked(payload):
    low = payload.lower()
    return any(bad.lower() in low for bad in BLACKLIST)

@app.route("/", methods=["GET", "POST"])
def fidelite():
    certificat = None
    error = None
    if request.method == "POST":
        nom = request.form.get("nom", "")
        if is_blocked(nom):
            error = "Entrée bloquée par le filtre de sécurité."
        else:
            # VULNÉRABLE : render_template_string sur une entrée utilisateur -> SSTI
            template = f"""
            <div class="certificat">
                <h3>Certificat de fidélité</h3>
                <p>Félicitations {nom}, vous êtes client(e) privilégié(e) du Café Saffran !</p>
            </div>
            """
            try:
                certificat = render_template_string(template)
            except Exception as e:
                error = f"Erreur de rendu : {e}"
    return render_template("form.html", certificat=certificat, error=error)

if __name__ == "__main__":
    with open("/flag.txt", "w") as f:
        f.write("FLAG{ssti_j1nj4_bl4ckl1st_byp4ss_rce}")
    app.run(host="0.0.0.0", port=5006)
