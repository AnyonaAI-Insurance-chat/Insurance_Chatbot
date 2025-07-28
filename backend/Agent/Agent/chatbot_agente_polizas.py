# chatbot_agente_polizas_ollama.py - Versión 100% gratuita

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool

load_dotenv()

# Cargar índice vectorial con embeddings gratuitos
def cargar_vectordb():
    path = "vector_index/"
    if not os.path.exists(path):
        raise FileNotFoundError("No se encontró el índice FAISS. Ejecuta primero indexador_ollama.py.")
    
    # Usar los mismos embeddings que en la indexación
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)

# Herramienta de consulta local
def crear_tool_pdf(vectordb):
    def consulta(query: str) -> str:
        docs = vectordb.similarity_search(query, k=3)
        print("\n[DEBUG] Chunks recuperados por similarity_search:")
        for i, doc in enumerate(docs):
            print(f"--- Chunk {i+1} ---")
            print("Contenido:", doc.page_content[:300], "..." if len(doc.page_content) > 300 else "")
            if hasattr(doc, "metadata"):
                print("Metadatos:", doc.metadata)
            print("-------------------")
        
        if not docs:
            return "❌ No encontré información relevante en los documentos de pólizas."

        contenido = "\n\n".join([doc.page_content for doc in docs])
        if len(contenido.strip()) < 100:
            return "❌ No encontré información clara en los documentos."

        return f"✅ Esto fue lo que encontré en los documentos de pólizas:\n\n{contenido}"

    return Tool(
        name="ConsultaPDF",
        func=consulta,
        description="Consulta en la base de conocimiento de pólizas"
    )

# Herramienta web
def crear_tool_web():
    return Tool(
        name="BusquedaEnLinea",
        func=DuckDuckGoSearchRun().run,
        description="Consulta en internet como último recurso"
    )

# Agente con Ollama - completamente gratuito
def responder(query: str, herramienta_pdf, herramienta_web, llm):
    system_prompt = (
        "Eres un agente de atención al cliente especializado en pólizas de seguros. "
        "Tu función es responder preguntas relacionadas únicamente con temas de seguros, pólizas, coberturas, derechos del asegurado, etc. "
        "Si el usuario hace preguntas que no tienen que ver con seguros, debes responder con cortesía indicando que no puedes ayudar con ese tema. "
        "Siempre debes responder con un tono amable, profesional, respetuoso y enfocado en ayudar al cliente. "
        "Responde en español de manera clara y concisa."
    )
    
    # Primero buscar en PDFs locales
    respuesta_pdf = herramienta_pdf.run(query)
    
    if "No encontré" in respuesta_pdf:
        print("\n[DEBUG] No se encontró info en PDFs, buscando en web...")
        respuesta_web = herramienta_web.run(query)
        prompt = f"""{system_prompt}

Pregunta del cliente: {query}

Información encontrada en internet: {respuesta_web}

Por favor, responde basándote en esta información, pero solo si está relacionada con seguros o pólizas. Si no está relacionada, indica cortésmente que no puedes ayudar con ese tema."""
    else:
        prompt = f"""{system_prompt}

Pregunta del cliente: {query}

Información encontrada en nuestros documentos de pólizas: {respuesta_pdf}

Por favor, responde basándote en esta información de nuestros documentos oficiales."""

    print("\n[DEBUG] Enviando prompt a Ollama...")
    try:
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        return f"❌ Error al conectar con Ollama: {e}. ¿Está corriendo el servicio?"

def main():
    print("🦙 Iniciando agente especializado en pólizas con Ollama (GRATIS)...")
    
    # Verificar que Ollama esté corriendo
    try:
        # Usar el modelo que tienes instalado
        llm = Ollama(
            model="llama3.2:latest",  # Puedes cambiar a "deepseek-r1:1.5b" si prefieres uno más rápido
            temperature=0.1
        )
        
        # Test rápido
        print("🔄 Probando conexión con Ollama...")
        test_response = llm.invoke("Hola")
        print("✅ Conexión exitosa con Ollama")
        
    except Exception as e:
        print(f"❌ Error conectando con Ollama: {e}")
        print("💡 Asegúrate de que Ollama esté corriendo: 'ollama serve' en otra terminal")
        return

    # Cargar herramientas
    try:
        vectordb = cargar_vectordb()
        tool_pdf = crear_tool_pdf(vectordb)
        tool_web = crear_tool_web()
        print("✅ Herramientas cargadas correctamente")
    except Exception as e:
        print(f"❌ Error cargando herramientas: {e}")
        return

    print("\n🤖 Agente listo para consultas sobre seguros y pólizas.")
    print("💡 Usando Ollama (completamente gratis) + embeddings de HuggingFace")
    print("Escribe 'salir' para terminar.\n")

    while True:
        pregunta = input("🧑 Tú: ")
        if pregunta.lower() in ["salir", "exit", "quit"]:
            break
        
        print("🔄 Procesando...")
        respuesta = responder(pregunta, tool_pdf, tool_web, llm)
        print(f"\n🤖 Agente:\n{respuesta}\n")

if __name__ == "__main__":
    main()