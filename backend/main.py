import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire():
    with open("templates/formulaire.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/generer", response_class=HTMLResponse)
async def generer(
    nom: str = Form(...),
    age: int = Form(...),
    sexe: str = Form(...),
    poids: float = Form(...),
    taille: float = Form(...),
    activite: str = Form(...),
    objectif: str = Form(...)
):
    prompt = (
        f"Crée un planning alimentaire simple pour {nom}, {age} ans, {sexe}, "
        f"{poids} kg, {taille} cm, activité: {activite}, objectif: {objectif}. "
        "Affiche-le sur 7 jours, avec matin/midi/soir, plats simples, grammages, "
        "et liens vers des recettes si possible."
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        planning = completion.choices[0].message["content"]
    except Exception as e:
        planning = f"Erreur lors de la génération : {e}"

    html_content = f"""
    <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
            <title>Planning généré</title>
        </head>
        <body>
            <a href="/" class="back-button">Retour à l’accueil</a>
            <div class="planning-content">{planning.replace('\n', '<br>')}</div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
