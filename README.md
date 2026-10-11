# CyberLab — Plateforme de Labs de Pentest Éducatifs

Environnement de lab pentest multi-conteneurs isolé, simulant des applications web vulnérables réelles (OWASP Top 10, contrôle d'accès cassé, injection), avec plateforme CTF intégrée pour le scoring et l'apprentissage.

**Stack :** Docker, Docker Compose, Flask/Python, CTFd, Ansible, sqlmap, Playwright, JWT

---

## Objectif du projet

Fournir un environnement pédagogique complet où les failles web classiques ne sont pas simulées par des applications tierces (DVWA, WebGoat), mais **développées sur-mesure** — chaque vulnérabilité est codée intentionnellement, documentée, et exploitable de bout en bout, du développement à l'exploitation jusqu'à la preuve (flag).

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Hôte Ubuntu (Docker)                │
│                                                         │
│  ┌──────────────┐        ┌─────────────────────────┐  │
│  │  Réseau       │        │   Réseau lab_targets     │  │
│  │  lab_attack   │        │   (challenges web)       │  │
│  │               │        │                           │  │
│  │  ┌─────────┐  │        │  sqli-login    :5000     │  │
│  │  │  Kali   │──┼────────┼─ cafe-menu-search :5001  │  │
│  │  │(conteneur│  │        │  cafe-avis     :5002     │  │
│  │  │ ou VM)   │  │        │  cafe-commandes :5003    │  │
│  │  └─────────┘  │        │  cafe-api      :5004     │  │
│  │               │        │  cafe-cv-upload :5005    │  │
│  └──────────────┘        └─────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  CTFd (CTF-FANAR) — scoring, challenges, flags    │  │
│  │  Port 8080                                         │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
            ▲
            │  VM Kali (attaquant externe)
            │  Réseau VMware Host-only
```

L'attaquant (VM Kali séparée) accède aux challenges exposés sur l'hôte Ubuntu via les ports publiés par Docker. Chaque challenge tourne dans son propre conteneur isolé.

## Challenges inclus

| # | Nom | Catégorie | Technique | Difficulté |
|---|---|---|---|---|
| 1 | Café Login — Bypass | SQLi | Injection SQL classique, bypass d'authentification | Facile |
| 2 | SQLi Avancée — UNION & Blind | SQLi | UNION-based avec bypass de filtre, blind boolean-based, sqlmap | Avancée |
| 3 | Avis Clients — Cookie Theft | XSS | XSS stocké, vol de cookie via bot admin headless | Moyenne |
| 4 | Mes Commandes — Accès Non Autorisé | Access Control | IDOR / BOLA | Facile |
| 5 | API Café — Forge ton accès | Access Control | Secret JWT faible, forge de token, BOLA | Avancée |
| 6 | Recrutement — Upload Non Filtré | RCE | Upload de fichier non filtré, webshell | Avancée |

Chaque challenge dispose d'un writeup détaillé dans `challenges/<nom>/writeup.md` (vulnérabilité, exploitation pas à pas, remédiation).

## Prérequis

- Ubuntu Server/Desktop (hôte Docker)
- VM Kali séparée (ou conteneur Kali) pour l'exploitation
- Ansible (installé automatiquement si absent)

## Installation

Déploiement complet automatisé via Ansible :

```bash
git clone https://github.com/jerbiiii/CyberLab cyberlab
cd cyberlab/ansible
sudo apt install -y ansible
ansible-playbook -i inventory.ini site.yml --ask-become-pass
```

Cela installe Docker si nécessaire, lance les 6 challenges, et démarre CTFd.

### Installation manuelle (alternative)

```bash
# 1. Lancer les challenges
cd compose
docker compose up -d --build

# 2. Lancer CTFd
cd ../CTFd
docker compose up -d
```

## Accès

- **CTFd (CTF-FANAR)** : `http://<ip-ubuntu>:8080`
- **Challenges individuels** : `http://<ip-ubuntu>:5000` à `5005`

## Structure du projet

```
cyberlab/
├── ansible/              # déploiement automatisé
│   ├── site.yml
│   ├── inventory.ini
│   └── roles/
├── compose/               # docker-compose des challenges
│   └── docker-compose.yml
├── challenges/             # un dossier par challenge
│   ├── sqli-login/
│   ├── cafe-menu-search/
│   ├── cafe-avis/
│   ├── cafe-commandes/
│   ├── cafe-api/
│   └── cafe-cv-upload/
│       ├── app.py
│       ├── Dockerfile
│       └── writeup.md
├── CTFd/                   # plateforme CTF (thème CTF-FANAR)
└── README.md
```

## Outils utilisés pour l'exploitation

- `curl` — requêtes HTTP manuelles
- `sqlmap` — automatisation de l'injection SQL blind
- Scripts Python (`pyjwt`) — cassage et forge de JWT
- Playwright — simulation réaliste d'un bot admin (exécution JS réelle)

## Avertissement

Projet à but éducatif uniquement. Lab isolé, à ne jamais exposer sur un réseau public. Toutes les vulnérabilités sont introduites volontairement à des fins d'apprentissage.

## Auteur

Yfz — Étudiant en ingénierie réseaux/sécurité (IDISC, ISI — Université de Tunis El Manar)
