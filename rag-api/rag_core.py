"""
rag_core.py
-----------
Toute la logique du RAG (indépendante de l'API).
"""

import os
import re
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

print(" Chargement du modèle d'embedding...")
modele_embedding = SentenceTransformer("all-MiniLM-L6-v2")

client_chroma = chromadb.PersistentClient(path="./chroma_db")
collection = client_chroma.get_or_create_collection(name="pdfs")


SEUIL_DOCUMENT_ENTIER = 40


def extraire_texte_pdf(chemin_pdf: str) -> str:
    reader = PdfReader(chemin_pdf)
    texte_complet = ""
    for page in reader.pages:
        texte_complet += page.extract_text() + "\n"
    return texte_complet


def decouper_en_chunks(texte: str, taille_max: int = 800):
    """
    Découpage 'intelligent' : on découpe d'abord par paragraphes (lignes vides),
    puis on regroupe les paragraphes entre eux jusqu'à atteindre taille_max,
    SANS jamais couper un paragraphe en plein milieu (sauf s'il est lui-même
    plus long que taille_max, auquel cas on le découpe en dernier recours).
    Ça évite de couper une idée ou une définition au mauvais endroit.
    """
    paragraphes = [p.strip() for p in re.split(r'\n\s*\n', texte) if p.strip()]

    chunks = []
    chunk_courant = ""

    for paragraphe in paragraphes:
        if len(chunk_courant) + len(paragraphe) + 1 <= taille_max:
            chunk_courant += ("\n" if chunk_courant else "") + paragraphe
        else:
            if chunk_courant:
                chunks.append(chunk_courant)
            if len(paragraphe) > taille_max:
                for i in range(0, len(paragraphe), taille_max):
                    chunks.append(paragraphe[i:i + taille_max])
                chunk_courant = ""
            else:
                chunk_courant = paragraphe

    if chunk_courant:
        chunks.append(chunk_courant)

    return chunks if chunks else [texte[:taille_max]]


def indexer_pdf(chemin_pdf: str, nom_document: str, proprietaire: str = "inconnu"):
    texte = extraire_texte_pdf(chemin_pdf)
    chunks = decouper_en_chunks(texte)
    embeddings = modele_embedding.encode(chunks).tolist()

    ids = [f"{nom_document}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": nom_document, "index": i, "owner": proprietaire} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    return len(chunks)


def _recuperer_document_entier(nom_document: str):
    """Récupère TOUS les chunks d'un document, triés dans leur ordre d'origine."""
    resultats = collection.get(where={"source": nom_document})

    def cle_de_tri(index_item):
        metadata, doc_id = index_item[0], index_item[1]
        if "index" in metadata:
            return metadata["index"]

        match = re.search(r'_chunk_(\d+)$', doc_id)
        return int(match.group(1)) if match else 0

    triplets = list(zip(resultats["metadatas"], resultats["ids"], resultats["documents"]))
    triplets.sort(key=lambda t: cle_de_tri((t[0], t[1])))

    return [texte for _, _, texte in triplets]


def retrouver_chunks_pertinents(question: str, nom_document: str = None, nb_resultats: int = 12):
    """
    Stratégie :
    - Si un document précis est demandé ET qu'il est assez petit -> on retourne
      TOUT son contenu (le LLM voit l'intégralité, plus aucune info ne peut manquer).
    - Sinon (document trop gros, ou recherche sur tous les documents) -> on revient
      à la recherche par similarité classique.
    """
    if nom_document:
        nb_chunks_total = collection.get(where={"source": nom_document})
        if len(nb_chunks_total["ids"]) <= SEUIL_DOCUMENT_ENTIER:
            return _recuperer_document_entier(nom_document)
        nb_resultats = 20

    embedding_question = modele_embedding.encode([question]).tolist()
    filtre = {"source": nom_document} if nom_document else None

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

    prompt = f"""Tu es un assistant qui répond à des questions à partir du contexte fourni ci-dessous.
IMPORTANT : réponds uniquement en texte brut, SANS Markdown (pas de tableaux, pas de **gras**, pas de <br>).
Le contexte peut contenir le document entier ou seulement des extraits pertinents.
Analyse bien l'intégralité du contexte fourni avant de répondre, y compris pour les questions
qui demandent de compter, lister, ou résumer plusieurs éléments du document.
Si la réponse ne se trouve vraiment pas dans le contexte, dis "Je ne trouve pas cette information dans le document."

Contexte :
{contexte}

Question : {question}

Réponse (en français, claire et concise) :"""

    reponse = client_groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return reponse.choices[0].message.content


def lister_documents_indexes(utilisateur: str = None, est_admin: bool = False):
    """
    Liste les documents indexés.
    - Si est_admin est True : retourne TOUS les documents, peu importe qui les a uploadés.
    - Sinon : retourne uniquement les documents uploadés par 'utilisateur'.
    """
    tout = collection.get()
    sources = set()
    for metadata in tout["metadatas"]:
        if est_admin or utilisateur is None:
            sources.add(metadata["source"])
        elif metadata.get("owner") == utilisateur:
            sources.add(metadata["source"])
    return list(sources)



def document_existe(nom_document: str) -> bool:
    """Vérifie si un document portant ce nom existe déjà, peu importe qui l'a uploadé."""
    resultats = collection.get(where={"source": nom_document})
    return len(resultats["ids"]) > 0






def supprimer_document(nom_document: str, utilisateur: str, est_admin: bool) -> str:
    """
    Retourne :
    - "ok" si suppression réussie
    - "introuvable" si le document n'existe pas
    - "interdit" si l'utilisateur n'est ni admin ni propriétaire
    """
    resultats = collection.get(where={"source": nom_document})
    if not resultats["ids"]:
        return "introuvable"

    proprietaire = resultats["metadatas"][0].get("owner")

    if not est_admin and proprietaire != utilisateur:
        return "interdit"

    collection.delete(where={"source": nom_document})

    chemin_fichier = os.path.join("uploaded_pdfs", nom_document)
    if os.path.exists(chemin_fichier):
        os.remove(chemin_fichier)

    return "ok"