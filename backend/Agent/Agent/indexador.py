# indexador.py - ChromaDB + Ollama (SIN OpenAI)

import os
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

def construir_y_guardar_vector_index():
    print("📥 Leyendo PDFs desde 'data/'...")
    archivos = [f for f in os.listdir("data") if f.endswith(".pdf")]
    if not archivos:
        print("❌ No hay archivos PDF en la carpeta 'data'.")
        return

    print(f"📚 Encontrados {len(archivos)} PDFs:")
    for archivo in archivos:
        print(f"   - {archivo}")

    # Cliente ChromaDB persistente
    print("🗄️ Inicializando ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_seguros")
    
    # Crear/obtener colección
    collection = client.get_or_create_collection(
        name="polizas_seguros",
        metadata={"description": "Documentos de pólizas de seguros"}
    )
    
    print("✅ Colección ChromaDB creada/conectada")

    # Cargar PDFs
    print("📖 Cargando contenido de PDFs...")
    loaders = [PyPDFLoader(f"data/{f}") for f in archivos]
    documentos = []
    for i, loader in enumerate(loaders):
        print(f"   Procesando {archivos[i]}...")
        try:
            docs = loader.load()
            documentos.extend(docs)
            print(f"      ✅ {len(docs)} páginas extraídas")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    print(f"✅ Total páginas cargadas: {len(documentos)}")

    # Dividir en chunks
    print("✂️ Dividiendo en chunks...")
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documentos)
    
    print(f"✅ Creados {len(chunks)} chunks de texto")

    # Preparar datos para ChromaDB
    print("🔄 Preparando datos para ChromaDB...")
    texts = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        texts.append(chunk.page_content)
        metadatas.append({
            "source": chunk.metadata.get("source", "unknown"),
            "page": chunk.metadata.get("page", 0),
            "chunk_id": i
        })
        ids.append(f"doc_{i}")

    # Agregar a ChromaDB (usa embeddings automáticos)
    print("💾 Guardando en ChromaDB...")
    print("   (ChromaDB generará embeddings automáticamente)")
    
    try:
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Agregados {len(texts)} chunks a ChromaDB")
        print("✅ Índice ChromaDB creado exitosamente en './chroma_seguros/'")
        print("🚀 Ahora puedes ejecutar: python main.py")
        
    except Exception as e:
        print(f"❌ Error guardando en ChromaDB: {e}")

if __name__ == "__main__":
    construir_y_guardar_vector_index()