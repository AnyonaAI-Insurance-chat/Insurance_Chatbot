import os
import asyncio
from typing import AsyncGenerator
import chromadb
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool

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

def crear_tool_buscador_noticias():
    """
    Crea una herramienta de búsqueda de noticias robusta que maneja queries vacíos.
    """
    # 1. Creamos una función "envoltorio" (wrapper)
    def buscar_noticias_seguras(query: str) -> str:
        # 2. La validación clave para evitar el crash
        if not query or not isinstance(query, str) or len(query.strip()) < 3:
            return "Para poder buscar noticias, necesito que me indiques un tema claro. Por ejemplo: 'noticias sobre seguros de ciberseguridad'."
        
        # 3. Si la validación pasa, ejecutamos la búsqueda real
        print(f"🔎 Buscando noticias en internet sobre: '{query}'")

        search_tool = DuckDuckGoSearchRun() 
        return search_tool.run(query)

    # 4. Creamos la herramienta con nuestra función segura
    return Tool(
        name="buscar_noticias_del_sector",
        func=buscar_noticias_seguras,
        description="Úsala cuando el usuario pida 'noticias', 'actualidad' o 'novedades' sobre un TEMA ESPECÍFICO de seguros. Esta herramienta requiere un término de búsqueda claro."
    )
def crear_tool_recombinador(collection, llm):
    def recombinar_coberturas(temas_a_combinar: str) -> str:
        """
        Busca varios textos de cobertura sobre los temas dados y los fusiona en uno nuevo.
        Ejemplo de input: 'cobertura de hospitalización y cobertura ambulatoria'
        """
        print(f"🤖 Recombinando coberturas para los temas: {temas_a_combinar}")
        try:
            # 1. Buscar fragmentos de texto para cada tema
            temas = [tema.strip() for tema in temas_a_combinar.split("y")]
            textos_encontrados = []
            for tema in temas:
                query = f"Artículo 2 sobre cobertura de {tema}"
                results = collection.query(query_texts=[query], n_results=2)
                if results and results.get('documents') and results['documents'][0]:
                    textos_encontrados.extend(results['documents'][0])
            
            if not textos_encontrados:
                return "No encontré suficientes textos de cobertura sobre los temas que mencionaste para poder crear una nueva póliza."

            contexto_unificado = "\n\n== FIN DE UN DOCUMENTO ==\n\n".join(textos_encontrados)

            # 2. Usar el LLM con un prompt específico para la tarea de fusión
            prompt_fusion = f"""Eres un abogado experto en seguros. Tu tarea es redactar un nuevo y único 'ARTÍCULO 2: COBERTURA' para una póliza de salud.
            Debes basarte EXCLUSIVAMENTE en los siguientes fragmentos de pólizas existentes. Combina las ideas, elimina redundancias y crea un texto coherente, claro y completo.
            El resultado debe ser un solo artículo unificado.

            FRAGMENTOS DE PÓLIZAS EXISTENTES:
            ---
            {contexto_unificado}
            ---

            NUEVO ARTÍCULO 2: COBERTURA (Redacción unificada):
            """
            
            # 3. Invocar al LLM para la tarea de generación
            response = llm.invoke(prompt_fusion)
            return response.content

        except Exception as e:
            return f"Ocurrió un error durante el proceso de recombinación: {e}"

    return Tool(
        name="crear_nueva_cobertura_combinada",
        func=recombinar_coberturas,
        description="Herramienta avanzada. Úsala SOLO cuando el usuario pida explícitamente 'crear una nueva póliza', 'combinar coberturas', 'fusionar artículos' o 'crear un ejemplo de cobertura' a partir de temas existentes."
    )

def crear_agente_executor(tools, llm):
    """
    Crea el agente y su ejecutor usando el método moderno y robusto `create_tool_calling_agent`.
    """
    # 1. El Prompt. Es más estructurado.
    #    Aquí definimos el personaje y las reglas de forma inamovible.
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres "Asistente Protege+", un especialista amable, empático y muy competente en pólizas de seguros. Tu objetivo es hacer que el usuario se sienta acompañado y comprendido.
        == TUS HERRAMIENTAS Y CUÁNDO USARLAS ==
        1.  `consultar_polizas_seguros`: Tu herramienta por defecto. Si la pregunta es sobre coberturas, condiciones, artículos o cualquier detalle de una póliza, esta es tu elección.
        2.  `buscar_noticias_del_sector`: Si el usuario menciona 'noticias', 'actualidad' o 'novedades' sobre un tema, usa esta herramienta. Asegúrate de extraer el tema de la pregunta del usuario para usarlo como término de búsqueda.
        3.  `crear_nueva_cobertura_combinada`: Misión especial. Úsala SOLO si el usuario pide explícitamente 'crear', 'combinar', 'fusionar' o 'hacer un ejemplo' de una nueva cobertura a partir de otras existentes.

        == TU PERSONALIDAD Y FORMA DE HABLAR ==
        - **Tono:** Eres profesional pero cercano. Usa un lenguaje claro y evita la jerga compleja.
        - **Proactividad:** Guía al usuario. Si una pregunta es ambigua, pide aclaración.
        - **Transparencia en la acción:** Comunica lo que estás haciendo. Usa frases como "Claro, déjame revisar los detalles en tu póliza.", "Entendido, consultando la información...".

        == REGLAS DE ORO (INQUEBRANTABLES) ==
        1.  **IDENTIDAD:** Eres "Asistente Protege+". Nunca menciones que eres una IA, un modelo o de Google. Si te preguntan sobre tu naturaleza, responde con amabilidad: "Soy Asistente Protege+, tu especialista en pólizas. Mi propósito es ayudarte a navegar tus documentos de seguro. ¿En qué te puedo ayudar?".
        2.  **FOCO:** Tu mundo son los seguros. Si la pregunta es de otro tema, recházala cortésmente.
        3.  **USO DE HERRAMIENTAS:** Para cualquier pregunta sobre seguros, tu acción principal es usar la herramienta `consultar_polizas_seguros`.

        == ESTRUCTURA DE RESPUESTA (Cuando encuentras información) ==
        1.  Confirma la recepción de la pregunta.
        2.  Presenta la información de forma clara, resumiendo y usando viñetas.
        3.  Cierra con una pregunta abierta para invitar a seguir la conversación.

        # ================================================================= #
        # === REGLA CRÍTICA: MANEJO DE CONVERSACIÓN Y MEMORIA CONTEXTUAL ==== #
        # ================================================================= #
        PRESTA MUCHA ATENCIÓN al historial del chat (`chat_history`). Las preguntas cortas del usuario como 'y por qué?', 'dónde dice eso?', 'pero de que articulo es?' o 'y sobre la cobertura X?' NO tienen sentido por sí solas.
        ANTES DE RESPONDER, DEBES leer los mensajes anteriores para entender el contexto completo.

        EJEMPLO DE RAZONAMIENTO CORRECTO:
        - Historial: El usuario acaba de enviar el texto "Los reembolsos se efectuarán...".
        - Pregunta Actual: "pero de que articulo es?"
        - TU PENSAMIENTO: 'La pregunta 'de qué artículo es' se refiere al texto sobre 'reembolsos' que el usuario me dio justo antes. Mi tarea es tomar ese texto y buscarlo con mi herramienta `consultar_polizas_seguros` para encontrar su ubicación en la póliza.'
        
        Si el usuario te da un texto de la póliza y luego te pregunta dónde está, TU DEBER es usar la herramienta para buscar ESE texto.
        """),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 2. Creamos el agente. Este agente está diseñado para llamar a herramientas.
    agent = create_tool_calling_agent(llm, tools, prompt)

    # 3. Creamos el ejecutor del agente, que maneja el ciclo de ejecución.
    #    La memoria se pasa aquí.
    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True, 
        output_key="output"
    )
    
    return AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        memory=memory,
        handle_parsing_errors=True # Muy importante para producción
    )

# --- CONFIGURACIÓN GLOBAL  ---



collection = cargar_chromadb()




# 2. Crear las herramientas
tool_chromadb = crear_tool_chromadb(collection)
tool_web = crear_tool_web()
tools = [tool_chromadb, tool_web]

# 3. Configurar el LLM
# Usamos una variable de entorno para la URL de Ollama, con un valor por defecto
# para que Docker pueda comunicarse con el Ollama que corre en el host (tu PC).

google_api_key = os.getenv("GOOGLE_API_KEY") 
if not google_api_key:
    raise ValueError("La variable de entorno GOOGLE_API_KEY no está configurada.")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest", # O el modelo de Gemini que prefieras
    google_api_key=google_api_key,

    temperature=0.0,

    temperature=0.1,
    convert_system_message_to_human=True # Útil para compatibilidad con algunos agentes

)


print("✅ Lógica del agente y herramientas inicializadas.")


tools = [
    crear_tool_chromadb(collection),
    crear_tool_buscador_noticias(),
    crear_tool_recombinador(collection, llm) 
]

# =========================================================================
# === FIN: LÓGICA ORIGINAL --- INICIO: CAPA DE CONEXIÓN WEB (Streaming) ===
# =========================================================================


async def get_agent_response(question: str, session_id: str) -> AsyncGenerator[str, None]:
    """

    Función puente que ahora usa el `AgentExecutor` con el agente `Tool Calling`.
    """
    # Creamos una instancia fresca del ejecutor para cada petición para mantener el estado aislado.
    agent_executor = crear_agente_executor(tools, llm)

    async for chunk in agent_executor.astream({"input": question}):
        # La salida de astream puede variar, buscamos la respuesta final en 'output'
        if "output" in chunk:
            cleaned_output = chunk["output"].replace("```", "").strip()
            if cleaned_output:
                yield cleaned_output

    Función "puente" que usa las funciones del equipo de IA para responder
    a una petición web de forma asíncrona y con streaming, usando el método nativo
    de LangChain `.astream()`.
    """
    # Creamos una instancia fresca del agente para cada petición.
    # Ya no necesitamos pasarle el callback.
    agent_executor = crear_agente(tools, llm)

    # El método .astream() es un generador asíncrono que devuelve
    # los pasos del pensamiento del agente en tiempo real.
    async for chunk in agent_executor.astream({"input": question}):
        # El agente devuelve diferentes tipos de "chunks" (pasos de acción, observaciones, etc.)
        # A nosotros solo nos interesa el chunk final que contiene la respuesta del LLM.
        # Este chunk se identifica porque tiene la clave "output".
        if "output" in chunk:
            # Hacemos yield de cada trozo de la respuesta final a medida que llega.
            yield chunk["output"]

