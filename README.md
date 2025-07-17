# Insurance Chatbot

A comprehensive insurance chatbot system with backend API, frontend interface, and vector database for document processing.

## Project Structure

```
Insurance_Chatbot/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Chatbot logic, LangChain agent
│   ├── services/           # External service clients (AWS, etc.)
│   ├── templates/          # HTML templates for the frontend
│   ├── static/             # CSS and JS
│   ├── main.py             # Your FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # React frontend
│   ├── src/                # Source code
│   ├── public/             # Public assets
│   ├── components/         # React components
│   ├── pages/              # Page components
│   ├── styles/             # CSS styles
│   └── Dockerfile          # Frontend container
├── vector_db/              # Vector database
│   ├── data/               # Data storage
│   ├── embeddings/         # Embedding files
│   ├── indexes/            # Vector indexes
│   └── Dockerfile          # Vector DB container
├── scripts/                # Utility scripts
│   └── ingest_data.py      # Script to process PDFs and put them into the vector DB
├── data/                   # (Optional) to temporarily store PDFs
├── docker-compose.yml      # Docker Compose configuration
└── .env                    # Environment variables
```

## Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your API keys
3. Run `docker-compose up` to start all services

## Services

- **Backend**: FastAPI server running on port 8000
- **Frontend**: React app running on port 3000
- **Database**: PostgreSQL running on port 5432
- **Vector DB**: Qdrant vector database running on port 6333 