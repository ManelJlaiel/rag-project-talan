"""
code_explainer_core.py

"""

import os
import re
import shutil
import subprocess
import tempfile
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))


DOSSIERS_IGNORES = {".git", "node_modules", "venv", "__pycache__", "dist", "build", "target", ".idea", ".vscode"}


FICHIERS_CONFIG_SERVICE = {
    "package.json": "Node.js/JavaScript",
    "pom.xml": "Java/Maven (Spring probable)",
    "build.gradle": "Java/Gradle (Spring probable)",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
}


PATTERNS_ENDPOINTS = [
    
    (r'@(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)', "FastAPI/Flask"),
    
    (r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(\s*["\']?([^"\')\s]*)', "Spring"),
   
    (r'(?<!@)(?:app|router)\.(get|post|put|delete)\(\s*["\']([^"\']+)', "Express"),
  
    (r'path\(\s*["\']([^"\']*)["\']', "Django"),
]


def cloner_repo(url_github: str) -> str:
    """Clone le repo dans un dossier temporaire et retourne le chemin."""
    dossier_temp = tempfile.mkdtemp(prefix="code_explainer_")
    resultat = subprocess.run(
        ["git", "clone", "--depth", "1", url_github, dossier_temp],
        capture_output=True, text=True, timeout=60
    )
    if resultat.returncode != 0:
        shutil.rmtree(dossier_temp, ignore_errors=True)
        raise ValueError(f"Impossible de cloner le repo : {resultat.stderr}")
    return dossier_temp


def lire_readme(chemin_repo: str) -> str:
    """Cherche et lit le README (plusieurs orthographes possibles)."""
    for nom in ["README.md", "README.rst", "README.txt", "readme.md", "README"]:
        chemin = os.path.join(chemin_repo, nom)
        if os.path.exists(chemin):
            with open(chemin, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:3000]  
    return "Aucun README trouvé."


def detecter_services_et_technos(chemin_repo: str):
    """Parcourt le repo pour trouver les fichiers de config = indices de services/technos."""
    services_trouves = []
    for racine, dossiers, fichiers in os.walk(chemin_repo):
        dossiers[:] = [d for d in dossiers if d not in DOSSIERS_IGNORES]
        for fichier in fichiers:
            if fichier in FICHIERS_CONFIG_SERVICE:
                chemin_relatif = os.path.relpath(racine, chemin_repo)
                services_trouves.append({
                    "dossier": chemin_relatif if chemin_relatif != "." else "(racine)",
                    "technologie": FICHIERS_CONFIG_SERVICE[fichier],
                    "fichier_config": fichier,
                })
    return services_trouves


def detecter_endpoints(chemin_repo: str, extensions_valides=(".py", ".java", ".js", ".ts")):
    """Scanne les fichiers de code et détecte les endpoints API via regex."""
    endpoints_trouves = []
    for racine, dossiers, fichiers in os.walk(chemin_repo):
        dossiers[:] = [d for d in dossiers if d not in DOSSIERS_IGNORES]
        for fichier in fichiers:
            if not fichier.endswith(extensions_valides):
                continue
            chemin_fichier = os.path.join(racine, fichier)
            try:
                with open(chemin_fichier, "r", encoding="utf-8", errors="ignore") as f:
                    contenu = f.read()
            except Exception:
                continue

            for pattern, framework in PATTERNS_ENDPOINTS:
                for match in re.finditer(pattern, contenu):
                    methode = match.group(1)
                    route = match.group(2) if len(match.groups()) > 1 else ""
                    chemin_relatif = os.path.relpath(chemin_fichier, chemin_repo)
                    endpoints_trouves.append({
                        "methode": methode.upper(),
                        "route": route,
                        "fichier": chemin_relatif,
                        "framework": framework,
                    })
    vus = set()
    endpoints_uniques = []
    for e in endpoints_trouves:
        cle = (e["methode"], e["route"], e["fichier"])
        if cle not in vus:
            vus.add(cle)
            endpoints_uniques.append(e)
    return endpoints_uniques


def construire_arbre_dossiers(chemin_repo: str, profondeur_max: int = 2) -> str:
    """Génère une représentation simple de l'arborescence (limitée en profondeur)."""
    lignes = []
    niveau_racine = chemin_repo.rstrip(os.sep).count(os.sep)

    for racine, dossiers, fichiers in os.walk(chemin_repo):
        dossiers[:] = [d for d in dossiers if d not in DOSSIERS_IGNORES]
        niveau = racine.count(os.sep) - niveau_racine
        if niveau > profondeur_max:
            dossiers[:] = []  
            continue
        indent = "  " * niveau
        nom_dossier = os.path.basename(racine) or "."
        lignes.append(f"{indent}{nom_dossier}/")
        for fichier in fichiers[:10]:  
            lignes.append(f"{indent}  {fichier}")

    return "\n".join(lignes[:100])  


def generer_resume(readme: str, services: list, endpoints: list, arbre: str) -> str:
    """Envoie tout le contexte collecté au LLM pour générer un résumé structuré."""

    texte_services = "\n".join(
        f"- {s['dossier']} → {s['technologie']} (fichier: {s['fichier_config']})"
        for s in services
    ) or "Aucun service détecté clairement."

    texte_endpoints = "\n".join(
        f"- [{e['methode']}] {e['route']} (fichier: {e['fichier']}, framework: {e['framework']})"
        for e in endpoints[:30]  
    ) or "Aucun endpoint détecté automatiquement."

    prompt = f"""Tu es un assistant qui analyse un projet de code à partir des informations suivantes et génère un résumé clair et structuré en français.

IMPORTANT : réponds uniquement en texte brut, SANS Markdown (pas de tableaux, pas de **gras**, pas de <br>, pas de #titres). Utilise uniquement des tirets simples (-) pour les listes et des retours à la ligne pour structurer.

README du projet :
{readme}

Arborescence du projet (partielle) :
{arbre}

Services / technologies détectés (via fichiers de config) :
{texte_services}

Endpoints API détectés automatiquement :
{texte_endpoints}

Génère un résumé structuré avec ces sections :
1. **Objectif du projet** (basé sur le README)
2. **Technologies utilisées**
3. **Architecture / services identifiés**
4. **Endpoints API principaux** (liste-les clairement)
5. **Points clés à retenir**

Si une information manque, dis-le clairement plutôt que d'inventer."""

    reponse = client_groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return reponse.choices[0].message.content


def analyser_repo(url_github: str) -> dict:
    """Fonction principale : orchestre toutes les étapes."""
    chemin_repo = cloner_repo(url_github)
    try:
        readme = lire_readme(chemin_repo)
        services = detecter_services_et_technos(chemin_repo)
        endpoints = detecter_endpoints(chemin_repo)
        arbre = construire_arbre_dossiers(chemin_repo)

        resume = generer_resume(readme, services, endpoints, arbre)

        return {
            "resume": resume,
            "services_detectes": services,
            "endpoints_detectes": endpoints,
        }
    finally:
        # Toujours nettoyer le dossier temporaire, même si erreur
        shutil.rmtree(chemin_repo, ignore_errors=True)