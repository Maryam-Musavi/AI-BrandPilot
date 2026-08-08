# AI BrandPilot - Setup Guide

## Prerequisites

- Python 3.10+
- Ollama installed and running locally
- Node.js (optional, for frontend)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
- `OLLAMA_HOST`: URL of your local Ollama server (default: http://127.0.0.1:11434)
- `EMBEDDING_MODEL`: Model for embeddings (default: nomic-embed-text)
- `LLM_MODEL`: Model for chat completions (default: llama3.2)
- `DATABASE_URL`: Database connection string

### 3. Pull Required Ollama Models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Root: http://localhost:8000/
- Health Check: http://localhost:8000/health
- Chat: http://localhost:8000/chat (POST)

### 5. Run Tests

```bash
pytest tests/ -v
```

### 6. Run Scheduler (Optional)

For automated LinkedIn workflows:

```bash
python scheduler.py
```

## Directory Structure

```
/workspace
├── app/                    # Main application code
│   ├── agent/             # AI agents
│   ├── config/            # Configuration
│   ├── knowledge/         # RAG and document processing
│   ├── memory/            # Conversation and knowledge storage
│   ├── models/            # Pydantic models
│   ├── prompts/           # Prompt templates
│   ├── services/          # Business logic services
│   └── tools/             # External integrations
├── data/                   # SQLite database storage
├── docs/                   # Documentation
├── tests/                  # Test suite
└── requirements.txt        # Python dependencies
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| POST | `/chat` | Send a message and get AI response |

## Features

- **Chat Interface**: Interactive conversation with AI assistant
- **Conversation Memory**: Persistent chat history in SQLite
- **Knowledge Base**: RAG-powered document search (txt, md files)
- **LinkedIn Workflow**: Automated weekly content planning
- **Multiple Agents**: Specialized agents for content, research, and LinkedIn
- **Local AI**: Runs entirely on local Ollama server (no cloud APIs required)
