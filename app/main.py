from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import html

# ¡LA IMPORTACIÓN CORRECTA!
# Solo importamos la función que realmente existe en chatbot_logic.py
from .chatbot_logic import get_agent_response

app = FastAPI(title="Insurance Chatbot API")

# Servir el frontend (esto se queda igual)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

class ChatRequest(BaseModel):
    question: str

# --- EL STREAM WRAPPER VIVE AQUÍ ---
# Esta función se encarga de la presentación (añadir los divs)
async def stream_wrapper(question: str, session_id: str):
    """
    Este generador envuelve la respuesta del agente para añadir el formato HTML
    que necesita el frontend con HTMX para el efecto "escribiendo".
    """
    # 1. Envía la apertura de la burbuja de mensaje.
    yield '<div class="message bot-message">'

    # 2. Itera sobre los tokens de texto puro que devuelve el agente.
    async for token in get_agent_response(question, session_id):
        # Escapa el token para evitar inyección de HTML y lo envía.
        yield html.escape(token)

    # 3. Envía el cierre de la burbuja.
    yield '</div>'


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    session_id = "user123" # Placeholder
    # Llamamos a nuestro nuevo stream_wrapper
    return StreamingResponse(stream_wrapper(req.question, session_id), media_type="text/html")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API is running!"}
