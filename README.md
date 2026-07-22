# Assistant Documentaire IA — RAG multi-fonctionnel

Projet de stage réalisé chez **Talan**. Système RAG (Retrieval-Augmented Generation) permettant :
1. D'uploader des PDFs et de poser des questions sur leur contenu
2. D'analyser un repository GitHub (résumé, technologies, endpoints détectés)

## Architecture

```
Angular (port 4200)
        │
        ▼
Spring Cloud Gateway (port 8082)
        │
        ├── /api/pdf/**  ──▶ Microservice PDF-RAG (port 8000, FastAPI)
        │                       └── ChromaDB (vectoriel) + Groq (LLM)
        │
        └── /api/code/** ──▶ Microservice Code Explainer (port 8001, FastAPI)
                                └── Clone GitHub + Groq (LLM)
```

## Technologies utilisées

| Composant | Technologies |
|---|---|
| Frontend | Angular 21, TypeScript, standalone components |
| Gateway | Spring Boot 4, Spring Cloud Gateway (WebFlux) |
| Microservices | Python, FastAPI, Uvicorn |
| Recherche vectorielle | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, local, gratuit) |
| LLM | Groq (`llama-3.1-8b-instant`) |
| Parsing PDF | pypdf |

## Prérequis

- Python 3.12+
- Node.js 20+ et Angular CLI
- Java 17+ et IntelliJ IDEA (ou autre IDE Java)
- Git
- Une clé API Groq (gratuite) — https://console.groq.com

## Installation et lancement

Le projet est composé de 4 services indépendants à lancer **dans cet ordre** :

### 1. Microservice PDF-RAG (port 8000)

```bash
cd rag-api
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine avec :
```
GROQ_API_KEY=votre_cle_ici
```

Lancer :
```bash
uvicorn main:app --reload --port 8000
```

### 2. Microservice Code Explainer (port 8001)

```bash
cd code-explainer-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Même fichier `.env` avec la clé Groq.

Lancer :
```bash
uvicorn main:app --reload --port 8001
```

### 3. Spring Cloud Gateway (port 8082)

Ouvrir le projet `gateway-service` dans IntelliJ IDEA et lancer `GatewayServiceApplication`.

### 4. Frontend Angular (port 4200)

```bash
cd rag-frontend
npm install
ng serve
```

Puis ouvrir : **http://localhost:4200**

## Documentation des endpoints

### Microservice PDF-RAG (via Gateway : `/api/pdf/...`)

| Méthode | Route | Description |
|---|---|---|
| POST | `/upload` | Upload et indexation d'un PDF |
| POST | `/ask` | Pose une question (globale ou sur un document précis) |
| GET | `/documents` | Liste les documents indexés |
| GET | `/health` | Vérification de l'état du service |

### Microservice Code Explainer (via Gateway : `/api/code/...`)

| Méthode | Route | Description |
|---|---|---|
| POST | `/analyze` | Clone et analyse un repo GitHub (résumé, services, endpoints) |
| GET | `/health` | Vérification de l'état du service |

## Limites connues et pistes d'amélioration

- **Questions "globales" sur un document** (ex: *"combien de X dans ce fichier ?"*) : le RAG classique récupère les `k` chunks les plus proches sémantiquement de la question, ce qui peut manquer des informations situées dans d'autres parties du document. Palliatif actuel : élargir `k` à 15 quand un document précis est sélectionné. Piste d'amélioration : résumé hiérarchique (map-reduce sur les chunks) pour les questions d'agrégation.
- **Extraction PDF** : `pypdf` peut mal extraire le texte de PDFs à mise en page complexe (colonnes, images de texte). Piste : OCR en complément pour les PDFs scannés.
- **Détection d'endpoints** : basée sur des regex par framework (FastAPI/Flask, Spring, Express, Django) — fonctionne bien sur du code standard, mais peut manquer des patterns non conventionnels. Piste : parsing AST plus robuste par langage.
- **Gestion des erreurs frontend** : à renforcer (retry automatique, messages d'erreur plus détaillés selon le type d'échec).

## Auteur

Projet réalisé dans le cadre d'un stage chez Talan.
