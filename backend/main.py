from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.get("/")
async def read_root():
    file_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    return FileResponse(file_path)
