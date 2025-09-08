# Backend API

FastAPI backend for the Business Improvement Project Management system.

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

#### Option 1: Using the startup script (recommended)
```bash
python run_server.py
```

#### Option 2: Direct uvicorn command
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option 3: Python module execution
```bash
python main.py
```

### API Endpoints

- **GET /** - Hello World endpoint
- **GET /health** - Basic health check
- **GET /health/** - Detailed health status
- **POST /agent/act** - Agent action (placeholder)
- **POST /graph/patch** - Graph modification (placeholder)
- **GET /graph/query** - Graph query (placeholder)
- **GET /todo** - TODO list (placeholder)
- **POST /todo** - Create TODO (placeholder)

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Configuration

The server uses `config.json` for configuration. Key settings:
- `api_host`: Server host (default: "0.0.0.0")
- `api_port`: Server port (default: 8000)
- `api_reload`: Auto-reload on changes (default: true)
- `log_level`: Logging level (default: "info")

### Development

The server includes:
- CORS middleware for frontend integration
- Structured logging with file rotation
- Health check endpoints for monitoring
- Placeholder endpoints for future Phase 1 features

### Testing

Test the API endpoints:
```bash
# Hello World
curl http://localhost:8000/

# Health Check
curl http://localhost:8000/health

# Detailed Health
curl http://localhost:8000/health/
```
