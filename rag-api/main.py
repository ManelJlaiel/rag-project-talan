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
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from pydantic import BaseModel

import rag_core

app = FastAPI(title="PDF RAG Microservice")

DOSSIER_UPLOADS = "uploaded_pdfs"
os.makedirs(DOSSIER_UPLOADS, exist_ok=True)



class QuestionRequest(BaseModel):
    question: str
    document: str | None = None  



@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    x_user: str = Header(default="inconnu", alias="X-User"),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .pdf sont acceptés.")

    if rag_core.document_existe(file.filename):
        raise HTTPException(
            status_code=409,
            detail=f"Un document nommé '{file.filename}' existe déjà. Merci de renommer votre fichier avant de l'uploader.",
        )

    chemin_fichier = os.path.join(DOSSIER_UPLOADS, file.filename)

   
    with open(chemin_fichier, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

  
    nb_chunks = rag_core.indexer_pdf(chemin_fichier, nom_document=file.filename, proprietaire=x_user)

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
async def liste_documents(
    x_user: str = Header(default="inconnu", alias="X-User"),
    x_user_roles: str = Header(default="", alias="X-User-Roles"),
):
    print(f"🔍 DEBUG - X-User reçu: '{x_user}' | X-User-Roles reçu: '{x_user_roles}'")
    est_admin = "admin" in x_user_roles.split(",")
    documents = rag_core.lister_documents_indexes(utilisateur=x_user, est_admin=est_admin)
    return {"documents": documents}




@app.delete("/documents/{nom_document}")
async def supprimer_un_document(
    nom_document: str,
    x_user: str = Header(default="inconnu", alias="X-User"),
    x_user_roles: str = Header(default="", alias="X-User-Roles"),
):
    est_admin = "admin" in x_user_roles.split(",")
    resultat = rag_core.supprimer_document(nom_document, utilisateur=x_user, est_admin=est_admin)

    if resultat == "introuvable":
        raise HTTPException(status_code=404, detail=f"Document '{nom_document}' introuvable.")
    if resultat == "interdit":
        raise HTTPException(status_code=403, detail="Vous n'avez pas le droit de supprimer ce document.")

    return {"message": f"Document '{nom_document}' supprimé avec succès."}



@app.get("/health")
async def health():
    return {"status": "ok"}