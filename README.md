# Assistant Documentaire IA — RAG multi-fonctionnel

Projet de stage réalisé chez **Talan**. Système RAG (Retrieval-Augmented Generation) sécurisé permettant :
1. D'uploader des PDFs et de poser des questions sur leur contenu
2. D'analyser un repository GitHub (résumé, technologies, endpoints détectés)

## Architecture

```
Angular (4200) ──── connexion ────▶ Keycloak (8180, realm talan-stage)
        │                                    │
        ▼                          valide le token JWT
Spring Cloud Gateway (8082, OAuth2 Resource Server)
        │
        ├── /api/pdf/**  ──▶ Microservice PDF-RAG (8000, FastAPI)
        │                       └── ChromaDB (vectoriel) + Groq (LLM)
        │
        └── /api/code/** ──▶ Microservice Code Explainer (8001, FastAPI)
                                └── Clone GitHub + Groq (LLM)
```

## Technologies utilisées

| Composant | Technologies |
|---|---|
| Frontend | Angular 21, TypeScript, standalone components, `angular-oauth2-oidc` |
| Authentification | Keycloak 26 (Docker), OAuth2 / OpenID Connect, Authorization Code Flow |
| Gateway | Spring Boot 4, Spring Cloud Gateway (WebFlux), Spring Security (Resource Server) |
| Microservices | Python, FastAPI, Uvicorn |
| Recherche vectorielle | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, local, gratuit) |
| LLM | Groq (`openai/gpt-oss-20b`) |
| Parsing PDF | pypdf |

> **Note de migration** : le modèle `llama-3.1-8b-instant` a été décommissionné par Groq le 16/08/2026. Le projet utilise désormais `openai/gpt-oss-20b`, le modèle de remplacement recommandé.

## Prérequis

- Python 3.12+
- Node.js 20+ et Angular CLI
- Java 17+ et IntelliJ IDEA (ou autre IDE Java)
- Docker Desktop (pour Keycloak)
- Git
- Une clé API Groq (gratuite) — https://console.groq.com

## Installation et lancement

Le projet est composé de 6 éléments à lancer **dans cet ordre** :

### 1. Docker Desktop
Lancer l'application, attendre qu'elle soit prête.

### 2. Keycloak (port 8180)

Premier lancement :
```bash
docker run -d --name keycloak -p 8180:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:26.0 start-dev
```

Lancements suivants :
```bash
docker start keycloak
```

Configuration réalisée dans l'interface admin (`http://localhost:8180`) :
- Realm : `talan-stage`
- Client : `rag-frontend` (public, Standard Flow, redirect URI `http://localhost:4200/*`)
- Utilisateur de test créé manuellement

### 3. Microservice PDF-RAG (port 8000)

```bash
cd rag-api
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Nécessite un fichier `.env` avec `GROQ_API_KEY=votre_cle`.

### 4. Microservice Code Explainer (port 8001)

```bash
cd code-explainer-api
venv\Scripts\activate
uvicorn main:app --reload --port 8001
```

Même fichier `.env`.

### 5. Spring Cloud Gateway (port 8082)

Lancer `GatewayServiceApplication` depuis IntelliJ IDEA.

### 6. Frontend Angular (port 4200)

```bash
cd rag-frontend
ng serve
```

Puis ouvrir : **http://localhost:4200** — un écran de connexion Keycloak s'affiche avant l'accès à l'application.

## Documentation des endpoints

### Microservice PDF-RAG (via Gateway : `/api/pdf/...`)

| Méthode | Route | Description | Authentification |
|---|---|---|---|
| POST | `/upload` | Upload et indexation d'un PDF | Requise |
| POST | `/ask` | Pose une question (globale ou sur un document précis) | Requise |
| GET | `/documents` | Liste les documents indexés | Requise |
| DELETE | `/documents/{nom}` | Supprime un document (index + fichier) | Requise |
| GET | `/health` | Vérification de l'état du service | Publique |

### Microservice Code Explainer (via Gateway : `/api/code/...`)

| Méthode | Route | Description | Authentification |
|---|---|---|---|
| POST | `/analyze` | Clone et analyse un repo GitHub | Requise |
| GET | `/health` | Vérification de l'état du service | Publique |

## Fonctionnalités ajoutées depuis la première version

- **Authentification Keycloak** : toute l'application est désormais protégée par un flux OAuth2/OIDC complet (voir section Sécurité ci-dessous)
- **Suppression de documents** : possibilité de retirer un PDF de l'index directement depuis l'interface
- **Historique de conversation persistant et par document** : chaque document a son propre fil de discussion, sauvegardé dans le navigateur (localStorage) et conservé après rafraîchissement
- **Chunking amélioré** : découpage par paragraphes plutôt que par nombre de caractères fixe, pour ne plus couper une idée en plein milieu
- **Récupération intégrale du document** : pour un document ciblé de taille raisonnable (≤ 40 chunks), le LLM reçoit désormais l'intégralité du texte plutôt que quelques extraits choisis par similarité — élimine la plupart des réponses "je ne trouve pas cette information" alors que l'info existe
- **Sortie forcée en texte brut** : les prompts contraignent désormais le LLM à répondre sans Markdown, pour un affichage propre dans l'interface

## Sécurité — Authentification Keycloak

L'application utilise un flux **OAuth2 Authorization Code Flow** :

1. L'utilisateur non connecté voit un écran de connexion dans Angular
2. Il est redirigé vers Keycloak, qui gère la saisie des identifiants (jamais vus par Angular)
3. Keycloak renvoie un code d'autorisation, échangé automatiquement contre un token JWT
4. Ce token est envoyé automatiquement (header `Authorization: Bearer ...`) à chaque requête vers la Gateway
5. La Gateway (configurée comme OAuth2 Resource Server) valide la signature du token auprès de Keycloak et n'autorise l'accès aux microservices qu'aux requêtes porteuses d'un token valide
6. Les routes `/health` restent publiques (monitoring), toutes les autres routes métier exigent une authentification

Les microservices Python eux-mêmes n'ont **aucune logique d'authentification** — la sécurité est entièrement centralisée au niveau de la Gateway, conformément au rôle qui lui avait été assigné dès la conception de l'architecture.

## Auteur

Projet réalisé dans le cadre d'un stage chez Talan.
