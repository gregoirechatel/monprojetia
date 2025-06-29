# backend/main.py
import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/formulaire")
async def get_form(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})


@app.post("/planning")
async def generate_planning(
    request: Request,
    nom: str = Form(...),
    age: str = Form(...),
    sexe: str = Form(...),
    poids: str = Form(...),
    taille: str = Form(...),
    objectif: str = Form(...),
    contraintes: str = Form(...)
):
    try:
        prompt = f"""Tu es un expert en nutrition. Crée un planning nutritionnel hebdomadaire simple et clair (petit-déjeuner, déjeuner, dîner) pour :
- Nom : {nom}
- Âge : {age}
- Sexe : {sexe}
- Poids : {poids} kg
- Taille : {taille} cm
- Objectif : {objectif}
- Contraintes alimentaires : {contraintes}
Donne uniquement le planning jour par jour, avec les plats, sans calories, sans justification, en format propre pour affichage HTML."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en nutrition"},
                {"role": "user", "content": prompt}
            ]
        )

        output = response.choices[0].message.content.strip()

        return templates.TemplateResponse("planning.html", {
            "request": request,
            "planning": output
        })

    except Exception as e:
        return templates.TemplateResponse("planning.html", {
            "request": request,
            "planning": f"Erreur lors de la génération du planning : {e}"
        })
