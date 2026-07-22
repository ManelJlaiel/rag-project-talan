"""
main.py
-------
API FastAPI qui expose le moteur RAG sous forme d'endpoints HTTP.
C'est CE fichier que ta gateway Spring Cloud appellera plus tard.

Lancer avec :
    uvicorn main:app --reload --port 8000

Documentation interactive auto-générée disponible sur :
    http://localhost:8000/docs
"""

import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

import rag_core

app = FastAPI(title="PDF RAG Microservice")

DOSSIER_UPLOADS = "uploaded_pdfs"
os.makedirs(DOSSIER_UPLOADS, exist_ok=True)



class QuestionRequest(BaseModel):
    question: str
    document: str | None = None  



@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .pdf sont acceptés.")

    chemin_fichier = os.path.join(DOSSIER_UPLOADS, file.filename)

   
    with open(chemin_fichier, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

  
    nb_chunks = rag_core.indexer_pdf(chemin_fichier, nom_document=file.filename)

    return {
        "message": f"PDF '{file.filename}' indexé avec succès.",
        "nb_chunks": nb_chunks,
    }



@app.post("/ask")
async def ask_question(requete: QuestionRequest):
    chunks_pertinents = rag_core.retrouver_chunks_pertinents(
        question=requete.question,
        nom_document=requete.document,
    )
    reponse = rag_core.generer_reponse(requete.question, chunks_pertinents)

    return {
        "question": requete.question,
        "reponse": reponse,
        "extraits_utilises": chunks_pertinents,
    }



@app.get("/documents")
async def liste_documents():
    documents = rag_core.lister_documents_indexes()
    return {"documents": documents}



@app.get("/health")
async def health():
    return {"status": "ok"}
