@echo off
start "" code .
call env\Scripts\activate.bat
cd backend
uvicorn main:app --reload
