from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import openai
import os

# Initialisation FastAPI
app = FastAPI()

# Fichiers statiques et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration de l'API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Accueil
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Formulaire
@app.get("/formulaire", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

# Traitement du formulaire
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
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        result = response.choices[0].message["content"]
    except Exception as e:
        result = f"Erreur lors de l’appel à l’API OpenAI : {e}"

    return templates.TemplateResponse("planning.html", {
        "request": request,
        "planning": result
    })
