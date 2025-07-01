from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import requests

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

@app.post("/planning", response_class=HTMLResponse)
async def planning(
    request: Request,
    objectif: str = Form(...),
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...)
):
    prompt = f"""
Tu es un expert en nutrition. Crée un planning hebdomadaire pour :
- Objectif : {objectif}
- Âge : {age} ans
- Poids : {poids} kg
- Taille : {taille} cm
- Sexe : {sexe}
- Niveau d’activité : {activite}

Le planning doit être structuré jour par jour (lundi à dimanche), matin, midi, soir, avec des idées de repas simples, grammages et liens si possible.
"""

    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=HEADERS, json=data)
        result = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        result = f"Erreur lors de l’appel à l’IA : {e}"

    return templates.TemplateResponse("planning.html", {
        "request": request,
        "planning": result
    })
