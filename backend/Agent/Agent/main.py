
from dotenv import load_dotenv
load_dotenv()

import os
import chromadb
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool, AgentType

try:
    from langchain_ollama import OllamaLLM as Ollama
except ImportError:
    from langchain_community.llms import Ollama

def obtener_ip_windows():
    import subprocess

    try:
        ip = subprocess.check_output("ip route show | grep -i default | awk '{ print $3}'", shell=True).decode().strip()
        return ip
    except:
        return None

def cargar_chromadb():
    try:
        client = chromadb.PersistentClient(path="./chroma_seguros")
        collection = client.get_collection("polizas_seguros")
        print(" Base de datos ChromaDB cargada")
        return collection
    except Exception as e:
        raise FileNotFoundError(f"No se encontró la base ChromaDB: {e}. Ejecuta primero indexador.py.")

def crear_tool_chromadb(collection):
    def consulta_chromadb(query: str) -> str:
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            
            if not results['documents'][0]:
                return " No encontré información relevante en los documentos de pólizas."

            contenido = "\n\n".join(results['documents'][0])
            
            if len(contenido.strip()) < 50:
                return " No encontré información clara en los documentos de pólizas."

            
            metadatos = ""
            if results['metadatas'] and results['metadatas'][0]:
                fuentes = set()
                for metadata in results['metadatas'][0]:
                    if metadata and 'source' in metadata:
                        fuentes.add(os.path.basename(metadata['source']))
                if fuentes:
                    metadatos = f"\n\n Fuentes: {', '.join(fuentes)}"

            return f" Información encontrada en documentos de pólizas:\n\n{contenido}{metadatos}"
            
        except Exception as e:
            return f" Error consultando ChromaDB: {e}"
    
    return Tool(
        name="ConsultaPDF",
        func=consulta_chromadb,
        description="HERRAMIENTA OBLIGATORIA: Busca información en documentos PDF de pólizas de seguros. DEBES usarla para TODA pregunta antes de responder. Contiene 267 chunks de información sobre seguros, pólizas, coberturas, derechos del asegurado, etc."
    )

def crear_tool_web():
    def busqueda_web(query: str) -> str:
        try:
            result = DuckDuckGoSearchRun().run(query)
            return f"Información de internet sobre '{query}':\n\n{result}"
        except Exception as e:
            return f"❌ Error en búsqueda web: {e}"
    
    return Tool(
        name="BusquedaEnLinea",
        func=busqueda_web,
        description="Busca información actualizada en internet. Úsala SOLO si no encuentras la respuesta en los PDFs de pólizas, o para información muy reciente."
    )

def crear_agente(tools, windows_ip):
    if windows_ip:
        llm = Ollama(
            model="llama3.2:latest",
            temperature=0.1,
            base_url=f"http://{windows_ip}:11434"
        )
    else:
        llm = Ollama(
            model="llama3.2:latest", 
            temperature=0.1,
            base_url="http://localhost:11434"
        )

    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )

    agente = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        max_iterations=3,
        early_stopping_method="generate",
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
    
    return agente

def main():
    print(" Iniciando Agente de Seguros con ChromaDB + Ollama...")
    print(" Base de datos vectorizada: 267 chunks de pólizas")
    
    windows_ip = obtener_ip_windows()
    print(f" IP de Windows detectada: {windows_ip}")
    
    try:
        if windows_ip:
            print(f" Probando conexión con {windows_ip}:11434...")
            llm_test = Ollama(model="llama3.2:latest", temperature=0, base_url=f"http://{windows_ip}:11434")
            test_response = llm_test.invoke("Hola")
            print(f" Conexión con Ollama exitosa (Windows IP: {windows_ip})")
        else:
            raise Exception("No se pudo obtener IP de Windows")
    except Exception as e:
        print(f" Error conectando con Ollama: {e}")
        print(" Verifica manualmente:")
        print(f"   curl http://{windows_ip}:11434/api/tags")
        print(" O instala Ollama en WSL:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        return

    try:
        collection = cargar_chromadb()
    except Exception as e:
        print(f" {e}")
        return

    herramienta_chromadb = crear_tool_chromadb(collection)
    herramienta_web = crear_tool_web()
    tools = [herramienta_chromadb, herramienta_web]

    try:
        print(" Inicializando agente conversacional...")
        agente = crear_agente(tools, windows_ip)
        print(" Agente listo con base vectorizada")
    except Exception as e:
        print(f" Error creando agente: {e}")
        return

    print("\n" + "="*60)
    print("  AGENTE ESPECIALIZADO EN SEGUROS Y PÓLIZAS")
    print("="*60)
    print(" Base de datos: ChromaDB vectorizada (267 chunks)")
    print(" LLM: Ollama local (gratis)")
    print(" Búsqueda: Semántica inteligente")
    print("\n Puedo ayudarte con:")
    print("   • Consultas sobre pólizas y coberturas")
    print("   • Derechos del asegurado")
    print("   • Procesos de reclamos")
    print("   • Información general sobre seguros")
    print("\n Escribe 'salir' para terminar")
    print("="*60)

    while True:
        try:
            pregunta = input("\n Tú: ").strip()
            
            if not pregunta:
                continue
                
            if pregunta.lower() in ["salir", "exit", "quit", "bye"]:
                print(" ¡Hasta pronto! Que tengas un buen día.")
                break
            
            print("\n Analizando tu consulta en la base vectorizada...")
            print("-" * 50)
            
            respuesta = agente.invoke({"input": pregunta})
            
            print("-" * 50)
            print(f" Agente Seguros:")
            print(f"{respuesta['output']}")
            
        except KeyboardInterrupt:
            print("\n\n Sesión interrumpida. ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n Error procesando consulta: {e}")
            print(" Intenta reformular tu pregunta")

if __name__ == "__main__":
    main()