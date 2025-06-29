from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import openai

app = FastAPI()

# Dossiers
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Clé API (via variable d’environnement Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/formulaire")
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

@app.post("/generate")
async def generate(request: Request, objectif: str = Form(...), preferences: str = Form(""), restrictions: str = Form("")):
    prompt = (
        f"Génère un planning nutritionnel simple sur 7 jours pour atteindre cet objectif : {objectif}.\n"
        f"Préférences : {preferences}.\n"
        f"Restrictions : {restrictions}.\n"
        f"Format : chaque jour avec matin, midi, soir, plats détaillés, grammages, et idées accessibles. "
        f"Ajoute un lien Marmiton pour les recettes plus élaborées."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        result = response.choices[0].message.content
    except Exception as e:
        result = f"Erreur lors de la génération : {str(e)}"

    return templates.TemplateResponse("planning.html", {"request": request, "result": result})
