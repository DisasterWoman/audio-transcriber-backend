# Audio Transcriber Backend

Backend API for an audio-to-text application.

The project is built as a production-minded FastAPI backend: users upload audio,
the API creates transcription jobs, stores job metadata in PostgreSQL, and exposes
job status/transcript endpoints for a future web or mobile frontend.

## Tech Stack

- Python 3.13
- FastAPI
- Pydantic
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose

## Project Structure

```text
app/
  api/            HTTP routes
  core/           settings/configuration
  db/             SQLAlchemy engine/session setup
  models/         database models
  repositories/   database access layer
  schemas/        Pydantic request/response schemas
  services/       business logic
alembic/          database migrations
```

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create local environment file

```bash
cp .env.example .env
```

### 4. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 5. Apply database migrations

```bash
.venv/bin/alembic upgrade head
```

### 6. Run the development server

```bash
fastapi dev app/main.py
```

## API Docs

After starting the server, open:

```text
http://127.0.0.1:8000/docs
```

## Useful Endpoints

```text
GET  /api/health
GET  /api/ready
GET  /api/languages/

GET   /api/jobs/
GET   /api/jobs/{job_id}
POST  /api/jobs/
POST  /api/jobs/upload
PATCH /api/jobs/{job_id}/status
PATCH /api/jobs/{job_id}/transcript
GET   /api/jobs/{job_id}/transcript
```

## Quick Smoke Test

Create a job:

```bash
curl -X POST http://127.0.0.1:8000/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "original_filename": "interview.mp3",
    "file_size_bytes": 123,
    "content_type": "audio/mpeg",
    "language": "en"
  }'
```

List jobs:

```bash
curl "http://127.0.0.1:8000/api/jobs/?language=en&limit=10"
```

Check database rows:

```bash
docker compose exec postgres psql -U transcriber -d audio_transcriber \
  -c "SELECT id, original_filename, status FROM jobs;"
```

## Database Migrations

Create a new migration after changing SQLAlchemy models:

```bash
.venv/bin/alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
.venv/bin/alembic upgrade head
```

## Notes

- `.env` is local and should not be committed.
- Uploaded files in `uploads/` are ignored by git.
- Local database/runtime data should not be committed.
