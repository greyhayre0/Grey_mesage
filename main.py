from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import engine
import models

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создаем таблицы, если их еще нет
models.Base.metadata.create_all(bind=engine)



@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/messager", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("messager.html", {"request": request})

@app.post("/register")
def register():
    pass

@app.get("/message")
def login():
    pass

@app.get("/nas")
def login():
    pass

@app.get("/exit")
def login():
    pass
