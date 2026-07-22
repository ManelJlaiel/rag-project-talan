"""
main.py
-------
API FastAPI qui expose le Code Explainer sous forme d'endpoint HTTP.

Lancer avec :
    uvicorn main:app --reload --port 8001

(Port 8001 car le microservice PDF-RAG tourne déjà sur 8000)

Documentation interactive :
    http://localhost:8001/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import code_explainer_core

app = FastAPI(title="Code Explainer Microservice")


class RepoRequest(BaseModel):
    github_url: str


@app.post("/analyze")
async def analyze_repo(requete: RepoRequest):
    try:
        resultat = code_explainer_core.analyser_repo(requete.github_url)
        return resultat
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur inattendue : {str(e)}")


@app.get("/health")
async def health():
    return {"status": "ok"}
