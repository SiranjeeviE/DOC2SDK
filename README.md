# Doc2SDK: AI-Powered API Integration Assistant

Doc2SDK is an intelligent API integration platform that automatically extracts API documentation, understands API behavior, generates production-ready SDK code, creates comprehensive test suites, and provides an interactive playground and change monitor for developers.

## 📺 Source

https://github.com/SiranjeeviE/Doc2SDK

## 🚀 Key Features

- **Multi-Source Extraction**:
  - **OpenAPI / Swagger**: Parse specifications in JSON and YAML formats (OpenAPI 3.0 / Swagger 2.0).
  - **Postman Collections**: Import Postman collection files (v2.0 / v2.1) directly into normalized API specifications.
  - **Web Documentation Scraping**: Scrapes online API documentation and extracts structured specifications using Google Gemini LLM.
  - **Direct File Upload**: Upload OpenAPI/Postman files up to 10MB directly from the dashboard or API.
- **Smart Code Generation**:
  - Generate production-grade, type-safe client SDKs in Python (`httpx`) and TypeScript (`axios`).
  - Built-in authentication support (Bearer token, API key headers/query params), timeouts, and retry logic.
- **Automated Testing Suite**:
  - Automatically generates executable unit and integration tests for every discovered endpoint.
  - Python test suites powered by `pytest` and `httpx` mock clients.
  - TypeScript test suites powered by `Jest` and mocked `axios`.
  - Comprehensive coverage including request parameters, bodies, 200 OK success, 400 Bad Request validation errors, and 500 Internal Server Error recovery.
- **API Change Monitoring & Breaking Change Detection**:
  - Tracks API schema evolution across versions (`v1`, `v2`, etc.).
  - Detects **breaking changes**: removed endpoints, modified HTTP methods, removed parameters, newly required parameters, altered parameter types, request body schema changes, and authentication changes.
  - Highlights non-breaking additions and modifications with severity badges.
  - Background change checks orchestrated via Celery and Redis.
- **Interactive Playground**:
  - Test endpoints live directly from the workspace UI.
  - Dynamic parameter substitution, header configuration, and JSON request body editor with execution history.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL, Redis, Celery.
- **Frontend**: React (Vite), TypeScript, Framer Motion, Lucide Icons.
- **AI / LLM**: Google Gemini (via `google-genai` async client) for intelligent doc parsing.

## 🏁 Getting Started

### Using Docker (Recommended)

```bash
docker-compose up --build
```
*Frontend runs on `http://localhost:5173` | Backend on `http://localhost:8000`*

### Manual Setup

1. **Backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Celery Worker (API Change Monitoring)**:
   ```bash
   cd backend
   celery -A tasks worker --loglevel=info
   ```

3. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   # Runs on http://localhost:5173
   ```

### Running Tests

- **Backend Test Suite (60 tests)**:
  ```bash
  cd backend
  pytest -v
  ```
- **Frontend Build Verification**:
  ```bash
  cd frontend
  npm run build
  ```

## 📂 Project Structure

- `backend/app/parsers/`: OpenAPI/Swagger (`openapi.py`) and Postman collection parser (`postman.py`).
- `backend/app/services/`: LLM extractor (`llm_parser.py`) and schema diffing (`diff.py`).
- `backend/app/generators/`: SDK and automated test generator (`sdk_gen.py`).
- `backend/app/routers/`: FastAPI endpoints (`projects.py`, `playground.py`, `unified.py`, `auth.py`).
- `backend/tasks.py`: Celery background tasks for async monitoring and scraping.
- `frontend/src/`: React UI, Workspace dashboard, API Change Monitor, and test explorer.

## 📄 License

MIT
