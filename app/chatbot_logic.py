# app/chatbot_logic.py
# Fiel adaptación del trabajo del equipo de IA para funcionar con FastAPI

import os
import asyncio
from typing import AsyncGenerator
import chromadb
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_ollama import OllamaLLM as Ollama 

# =========================================================================
# === INICIO: LÓGICA ORIGINAL DEL EQUIPO DE IA (Adaptada para Docker) ===
# =========================================================================

def cargar_chromadb():
    """
    Se conecta al servicio de ChromaDB que corre en Docker.
    """
    try:
        # CORRECCIÓN CLAVE: Apuntamos al servicio 'chromadb' de Docker
        client = chromadb.HttpClient(host='chromadb', port=8000)
        collection = client.get_collection("polizas_seguros")
        print("✅ Base de datos ChromaDB cargada y conectada desde Docker.")
        return collection
    except Exception as e:
        # En un entorno de servidor, es mejor lanzar la excepción para que se registre.
        print(f"❌ Error fatal al cargar ChromaDB: {e}")
        raise e

def crear_tool_chromadb(collection):
    """
    Crea la herramienta de LangChain para consultar la base de datos de pólizas.
    """
    def consulta_chromadb(query: str) -> str:
        try:
            results = collection.query(query_texts=[query], n_results=3)
            if not results['documents'][0]:
                return "No encontré información relevante en los documentos de pólizas."
            
            contenido = "\n\n".join(results['documents'][0])
            if len(contenido.strip()) < 50:
                 return "No encontré información clara en los documentos de pólizas."

            metadatos = ""
            if results['metadatas'] and results['metadatas'][0]:
                fuentes = {os.path.basename(m['source']) for m in results['metadatas'][0] if m and 'source' in m}
                if fuentes:
                    metadatos = f"\n\nFuentes: {', '.join(fuentes)}"
            return f"Información encontrada en documentos de pólizas:\n\n{contenido}{metadatos}"
        except Exception as e:
            return f"Error consultando ChromaDB: {e}"
    
    return Tool(
        name="ConsultaPDF",
        func=consulta_chromadb,
        description="HERRAMIENTA OBLIGATORIA: Busca información en documentos PDF de pólizas de seguros. DEBES usarla para TODA pregunta. Contiene 267 chunks de información sobre seguros, pólizas, coberturas, etc."
    )

def crear_tool_web():
    """
    Crea la herramienta de LangChain para buscar en internet.
    """
    return Tool(
        name="BusquedaEnLinea",
        func=DuckDuckGoSearchRun().run,
        description="Busca información actualizada en internet. Úsala SOLO si no encuentras la respuesta en los PDFs de pólizas, o para información muy reciente."
    )

def crear_agente(tools, llm, callbacks=None):
    """
    Crea e inicializa el agente conversacional de LangChain.
    Acepta callbacks opcionales para el streaming.
    """
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    return initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        max_iterations=3,
        callbacks=callbacks,
        agent_kwargs={
            "system_message": """Eres un agente especializado EXCLUSIVAMENTE en seguros y pólizas.

REGLAS ESTRICTAS:
1. SIEMPRE usa la herramienta ConsultaPDF PRIMERO para CUALQUIER pregunta.
2. Si la pregunta NO es sobre seguros/pólizas, responde: "Lo siento, solo puedo ayudar con temas de seguros y pólizas."
3. NUNCA respondas preguntas sobre constitución, leyes generales, o temas no relacionados con seguros.
4. SIEMPRE busca en la base de datos de pólizas antes de responder.

FLUJO OBLIGATORIO:
1. ¿Es sobre seguros? → SI: Usar ConsultaPDF → Responder
2. ¿Es sobre seguros? → NO: Rechazar cortésmente

Recuerda: Tienes 267 chunks de documentos de pólizas para consultar."""
        }
    )

# --- CONFIGURACIÓN GLOBAL (Se ejecuta una sola vez al iniciar la API) ---

# 1. Cargar la base de datos
collection = cargar_chromadb()

# 2. Crear las herramientas
tool_chromadb = crear_tool_chromadb(collection)
tool_web = crear_tool_web()
tools = [tool_chromadb, tool_web]

# 3. Configurar el LLM
# Usamos una variable de entorno para la URL de Ollama, con un valor por defecto
# para que Docker pueda comunicarse con el Ollama que corre en el host (tu PC).
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
llm = Ollama(
    model="llama3.2:latest",
    temperature=0.1,
    base_url=ollama_base_url
)

print("✅ Lógica del agente y herramientas inicializadas.")

# =========================================================================
# === FIN: LÓGICA ORIGINAL --- INICIO: CAPA DE CONEXIÓN WEB (Streaming) ===
# =========================================================================

class AsyncStreamCallbackHandler(AsyncCallbackHandler):
    """Callback handler para el streaming de tokens a una cola asyncio."""
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        await self.queue.put(token)
    async def on_llm_end(self, response, **kwargs) -> None:
        await self.queue.put(None)
    async def on_llm_error(self, error, **kwargs) -> None:
        await self.queue.put(None)

async def get_agent_response(question: str, session_id: str) -> AsyncGenerator[str, None]:
    """
    Función "puente" que usa las funciones del equipo de IA para responder
    a una petición web de forma asíncrona y con streaming.
    """
    queue = asyncio.Queue()
    
    # Creamos una instancia del agente para esta petición específica,
    # pasándole nuestro callback handler para el streaming.
    agent_executor = crear_agente(tools, llm, callbacks=[AsyncStreamCallbackHandler(queue)])

    # Ejecutamos el agente en una tarea de fondo para no bloquear la respuesta
    async def run_agent_in_background():
        try:
            # acall es la versión asíncrona de invoke/run
            await agent_executor.acall({"input": question})
        except Exception as e:
            print(f"Error en la ejecución del agente: {e}")
            await queue.put(None)

    asyncio.create_task(run_agent_in_background())

    # Consumimos de la cola y devolvemos los tokens al endpoint de FastAPI
    while True:
        token = await queue.get()
        if token is None:
            # Se recibió la señal de fin
            break
        yield token
