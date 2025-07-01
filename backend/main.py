import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route accueil
@app.get("/", response_class=HTMLResponse)
def lire_index():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

# Route pour afficher planning déjà généré
@app.get("/planning", response_class=HTMLResponse)
def lire_planning():
    with open("templates/planning.html", encoding="utf-8") as f:
        return f.read()

# Route pour afficher liste déjà générée
@app.get("/liste", response_class=HTMLResponse)
def lire_liste():
    with open("templates/liste.html", encoding="utf-8") as f:
        return f.read()

# Route POST pour générer planning + liste
@app.post("/generer", response_class=HTMLResponse)
def generer(
    objectif: str = Form(...),
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...),
    email: str = Form(...)
):
    prompt = f"""
Tu es un expert en nutrition. Génère un planning nutritionnel hebdomadaire clair, structuré (matin, midi, soir), avec les grammages, des plats simples et un lien Marmiton si possible.
Puis génère en-dessous une liste de courses complète avec les quantités en grammes, regroupée par type (féculents, légumes, protéines…).

Données utilisateur :
Objectif : {objectif}
Âge : {age}
Poids : {poids} kg
Taille : {taille} cm
Sexe : {sexe}
Niveau d’activité : {activite}
"""

    api_key = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://monprojetia.onrender.com",
        "Content-Type": "application/json"
    }

    body = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=30
        )
        response.raise_for_status()
        resultat = response.json()["choices"][0]["message"]["content"]

        planning_content = f"""
        <html>
        <head><meta charset="utf-8"><link rel="stylesheet" href="/static/style.css"></head>
        <body>
        <h1>Ton planning nutritionnel personnalisé</h1>
        <pre>{resultat}</pre>
        <a href="/">Retour à l'accueil</a>
        </body>
        </html>
        """

        liste_content = f"""
        <html>
        <head><meta charset="utf-8"><link rel="stylesheet" href="/static/style.css"></head>
        <body>
        <h1>Ta liste de courses complète</h1>
        <pre>{resultat}</pre>
        <a href="/">Retour à l'accueil</a>
        </body>
        </html>
        """

        with open("templates/planning.html", "w", encoding="utf-8") as f:
            f.write(planning_content)

        with open("templates/liste.html", "w", encoding="utf-8") as f:
            f.write(liste_content)

        return planning_content

    except Exception as e:
        return HTMLResponse(
            content=f"<p>Erreur lors de l’appel à l’IA : {e}</p><a href='/'>Retour à l'accueil</a>",
            status_code=500
        )
