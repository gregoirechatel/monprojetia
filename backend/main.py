from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os
import json

app = FastAPI()

# Configuration statiques & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 🔹 Page d’accueil
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 🔹 Formulaire
@app.get("/formulaire", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

# 🔹 Génération du planning via IA + sauvegarde
@app.post("/planning", response_class=HTMLResponse)
async def generate_planning(
    request: Request,
    objectif: str = Form(...),
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...)
):
    prompt = f"""
Tu es un expert en nutrition. Crée un planning nutritionnel hebdomadaire pour :
- Objectif : {objectif}
- Âge : {age} ans
- Poids : {poids} kg
- Taille : {taille} cm
- Sexe : {sexe}
- Niveau d’activité : {activite}

Le planning doit contenir des repas simples, équilibrés et adaptés à cet utilisateur.
Structure-le par jour (lundi à dimanche), avec matin / midi / soir, et donne des grammages approximatifs.
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1800
            }
        )

        data = response.json()
        result = data['choices'][0]['message']['content']

        # Sauvegarde du planning dans planning.json
        with open("backend/data/planning.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    except Exception as e:
        result = f"Erreur lors de l’appel à l’IA : {e}"

    return templates.TemplateResponse("planning.html", {
        "request": request,
        "planning": result
    })

# 🔹 Génération de la liste de courses
@app.get("/liste", response_class=HTMLResponse)
async def generate_liste(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            planning_data = f.read()

        prompt = f"""
Voici un planning nutritionnel :\n\n{planning_data}\n\n
Fournis-moi une liste de courses hebdomadaire complète en fonction de ce planning. 
Organise les ingrédients par catégorie (ex : Légumes, Féculents, Viandes…), avec les quantités approximatives en grammes. 
La liste doit être claire, lisible et exploitable en supermarché.
"""

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
        )

        data = response.json()
        liste_courses = data['choices'][0]['message']['content']

    except Exception as e:
        liste_courses = f"Erreur lors de la génération de la liste de courses : {e}"

    return templates.TemplateResponse("liste.html", {
        "request": request,
        "liste": liste_courses
    })
