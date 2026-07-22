"""
rag_core.py

"""

import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))


print("🧠 Chargement du modèle d'embedding...")
modele_embedding = SentenceTransformer("all-MiniLM-L6-v2")


client_chroma = chromadb.PersistentClient(path="./chroma_db")
collection = client_chroma.get_or_create_collection(name="pdfs")


def extraire_texte_pdf(chemin_pdf: str) -> str:
    reader = PdfReader(chemin_pdf)
    texte_complet = ""
    for page in reader.pages:
        texte_complet += page.extract_text() + "\n"
    return texte_complet


def decouper_en_chunks(texte: str, taille_chunk: int = 500, chevauchement: int = 50):
    chunks = []
    debut = 0
    while debut < len(texte):
        fin = debut + taille_chunk
        chunks.append(texte[debut:fin])
        debut += taille_chunk - chevauchement
    return chunks


def indexer_pdf(chemin_pdf: str, nom_document: str):
    """
    Indexe un PDF dans ChromaDB.
    nom_document = identifiant unique (ex: nom du fichier) pour retrouver
    plus tard à quel PDF appartient chaque chunk.
    """
    texte = extraire_texte_pdf(chemin_pdf)
    chunks = decouper_en_chunks(texte)
    embeddings = modele_embedding.encode(chunks).tolist()

   
    ids = [f"{nom_document}_chunk_{i}" for i in range(len(chunks))]

   
    metadatas = [{"source": nom_document} for _ in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    return len(chunks)


def retrouver_chunks_pertinents(question: str, nom_document: str = None, nb_resultats: int = 5):
    """
    Cherche les chunks les plus pertinents.
    Si nom_document est fourni, on augmente le nombre de résultats récupérés :
    comme la recherche est filtrée sur UN SEUL document (généralement petit),
    on peut se permettre d'en récupérer beaucoup plus pour mieux couvrir
    les questions "globales" (ex: "combien de X dans ce document ?").
    """
    embedding_question = modele_embedding.encode([question]).tolist()

    filtre = {"source": nom_document} if nom_document else None

    if nom_document:
        nb_resultats = 15  

    resultats = collection.query(
        query_embeddings=embedding_question,
        n_results=nb_resultats,
        where=filtre,
    )
    return resultats["documents"][0] if resultats["documents"] else []


def generer_reponse(question: str, chunks_pertinents: list) -> str:
    if not chunks_pertinents:
        return "Je ne trouve aucune information pertinente dans les documents indexés."

    contexte = "\n\n---\n\n".join(chunks_pertinents)

    prompt = f"""Tu es un assistant qui répond à des questions UNIQUEMENT à partir du contexte fourni ci-dessous.
Si la réponse ne se trouve pas dans le contexte, dis "Je ne trouve pas cette information dans le document."

Contexte :
{contexte}

Question : {question}

Réponse (en français, claire et concise) :"""

    reponse = client_groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return reponse.choices[0].message.content


def lister_documents_indexes():
    """Retourne la liste des noms de documents déjà indexés (sans doublons)."""
    tout = collection.get()
    sources = set()
    for metadata in tout["metadatas"]:
        sources.add(metadata["source"])
    return list(sources)