from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import openai
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Clé API OpenAI (gérée via Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

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
    prompt = (
        f"Crée un planning nutritionnel hebdomadaire personnalisé pour un(e) {sexe} de {age} ans, "
        f"{taille} cm, {poids} kg, avec un niveau d'activité {activite} et comme objectif : {objectif}. "
        f"Affiche seulement les repas (matin, midi, soir) pour chaque jour, sans calories visibles."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        output = response.choices[0].message["content"]
    except Exception as e:
        output = f"Erreur lors de la génération du planning : {e}"

    return templates.TemplateResponse("planning.html", {
        "request": request,
        "planning": output
    })
