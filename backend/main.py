from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()

# Dossier templates et static
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Clé OpenAI stockée sur Render dans les variables d'environnement
api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/planning")
async def planning(
    request: Request,
    nom: str = Form(...),
    age: int = Form(...),
    sexe: str = Form(...),
    poids: float = Form(...),
    taille: float = Form(...),
    objectif: str = Form(...)
):
    prompt = (
        f"Génère un planning alimentaire hebdomadaire pour {nom}, {sexe}, {age} ans, "
        f"{poids} kg pour {taille} cm, ayant pour objectif : {objectif}. "
        f"Propose des repas simples avec quantités précises pour chaque jour (matin, midi, soir)."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    data = response.json()

    try:
        planning_text = data["choices"][0]["message"]["content"]
    except Exception as e:
        planning_text = f"Erreur lors de la génération : {e}"

    return templates.TemplateResponse("planing.html", {"request": request, "planning": planning_text})
