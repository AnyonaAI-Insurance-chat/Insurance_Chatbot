from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import asyncio
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI(title="Insurance Chatbot API")

# --- CONFIGURACIÓN DE GEMINI ---
# Carga la clave de API desde las variables de entorno que Docker inyectó
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Una pequeña validación para asegurar que la clave está presente
    print("ERROR: La variable de entorno GOOGLE_API_KEY no está definida.")
else:
    genai.configure(api_key=api_key)

# Inicializamos un modelo. 'gemini-1.5-flash' es súper rápido e ideal para chat.
gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
# -------------------------------

# Montar archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Configurar plantillas Jinja2 para servir el HTML
templates = Jinja2Templates(directory="app/templates")

class ChatRequest(BaseModel):
    question: str

async def fake_streamer(question: str):
    """Simula una respuesta en streaming del LLM."""
    response_words = f"Recibí tu pregunta: '{question}'. Ahora mismo estoy simulando una respuesta...".split()
    for word in response_words:
        yield f'<div class="message bot-message">{word}</div>'
        await asyncio.sleep(0.1) # Simula el tiempo de generación

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Endpoint que recibe una pregunta y devuelve un stream de HTML."""
    # Aquí es donde, en el futuro, llamarás a la función de tu compañero de LangChain
    return StreamingResponse(fake_streamer(req.question), media_type="text/html")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Sirve el frontend principal."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
def health_check():
    """Endpoint de salud para saber si la API está viva."""
    return {"status": "ok", "message": "API is running!"}
    
# --- NUEVO ENDPOINT DE PRUEBA PARA GEMINI ---
@app.post("/api/test_gemini")
async def test_gemini_endpoint(req: ChatRequest):
    """
    Endpoint de prueba que envía una pregunta directamente a Gemini
    y devuelve la respuesta.
    """
    try:
        # Enviar la pregunta al modelo de Gemini
        response = gemini_model.generate_content(req.question)

        # Devolver el texto de la respuesta
        return {"response": response.text}
    except Exception as e:
        # Manejo básico de errores por si algo falla (ej. API key inválida)
        return {"error": f"Ha ocurrido un error con la API de Gemini: {str(e)}"}
