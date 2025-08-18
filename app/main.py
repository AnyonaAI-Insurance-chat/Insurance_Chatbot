from fastapi import FastAPI, Request, Cookie, Depends, Response
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
import html


# --- Importaciones locales (ahora correctas) ---
from .db import models, crud
from .db.database import SessionLocal, engine
from .security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES


from .chatbot_logic import get_agent_response

# --- Inicialización ---
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Insurance Chatbot API")


# --- Montaje de Archivos Estáticos y Plantillas ---
# IMPORTANTE: Esto se mueve a una sección propia después de inicializar la app.

# Servir el frontend 

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# --- Dependencias ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Modelos Pydantic ---
class ChatRequest(BaseModel):
    question: str
class UserForm(BaseModel):
    username: str
    password: str

# ===============================================================
# === RUTAS DE AUTENTICACIÓN Y PÁGINAS (Definidas PRIMERO) ===
# ===============================================================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, access_token: Optional[str] = Cookie(None)):
    # Si ya hay un token (el usuario ya ha iniciado sesión),
    # lo redirigimos a la página principal.
    if access_token:
        return RedirectResponse(url="/")
    
    # Si no, mostramos la página de login.
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, access_token: Optional[str] = Cookie(None)):
    # Hacemos la misma comprobación para la página de registro.
    if access_token:
        return RedirectResponse(url="/")

    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def handle_register(form_data: UserForm, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if user:
        html_content = '<li class="error">El nombre de usuario ya existe.</li>'
        return HTMLResponse(content=html_content)
    
    crud.create_user(db, username=form_data.username, password=form_data.password)
    html_content = '<li class="success">¡Registro exitoso! Ahora puedes <a href="/login">iniciar sesión</a>.</li>'
    return HTMLResponse(content=html_content)

@app.post("/login")
async def handle_login(form_data: UserForm, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Lógica de error (igual que en /register)
        html_content = '<li class="error">Nombre de usuario o contraseña incorrectos.</li>'
        return Response(content=html_content, media_type="text/html")
    
    # Lógica de éxito
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # --- ¡AQUÍ ESTÁ LA LÓGICA COPIADA Y ADAPTADA! ---
    # Usamos la clase base 'Response' igual que en el registro.
    html_content = '<li class="success">¡Login exitoso! Redirigiendo...</li>'
    response = Response(content=html_content, media_type="text/html")
    
    # Añadimos la cookie y el header a este objeto Response base.
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite='lax')
    response.headers["HX-Refresh"] = "true"
    
    return response
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="access_token")
    return response

# ===============================================================
# === RUTAS PRINCIPALES DE LA APLICACIÓN (Protegidas) ===
# ===============================================================

async def stream_wrapper(question: str, session_id: str):
    yield '<div class="message bot-message">'
    async for token in get_agent_response(question, session_id):
        yield html.escape(token)
    yield '</div>'

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        return RedirectResponse(url="/login")
    # Aquí iría la lógica de validación del token
    return templates.TemplateResponse("index.html", {"request": request})
    
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Aquí iría la lógica de validación del token
    session_id = "user123" # Placeholder
    return StreamingResponse(stream_wrapper(req.question, session_id), media_type="text/html")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API is running!"}
