from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/formulaire")
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})


@app.post("/formulaire")
async def handle_form(request: Request, nom: str = Form(...), objectif: str = Form(...)):
    prompt = f"Crée un planning nutritionnel simple pour {nom} avec l’objectif : {objectif}."
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    planning = completion.choices[0].message.content

    # Sauvegarde côté backend
    os.makedirs("backend/data", exist_ok=True)
    with open("backend/data/planning.json", "w") as f:
        json.dump({"content": planning}, f)

    return RedirectResponse("/planning", status_code=302)


@app.get("/planning")
async def planning(request: Request):
    with open("backend/data/planning.json", "r") as f:
        data = json.load(f)
    return templates.TemplateResponse("planning.html", {"request": request, "planning": data["content"]})
