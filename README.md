# Audio Transcriber Backend

Backend service for an audio-to-text web application.

## Tech stack

- Python 3.13
- FastAPI

## Features implemented

- Basic FastAPI app setup
- Health check endpoint
- Jobs API
  - `GET /jobs/`
  - `GET /jobs/{job_id}`
  - `POST /jobs/`
- Request validation with Pydantic
- Response schemas
- Service layer for job logic

## Project setup

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
2. Install dependencies
pip install -r requirements.txt
3. Run the development server
fastapi dev app/main.py
API docs

After starting the server, open:

http://127.0.0.1:8000/docs