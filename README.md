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
  core/           settings, errors, middleware
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
POST  /api/jobs/{job_id}/process
PATCH /api/jobs/{job_id}/status
PATCH /api/jobs/{job_id}/transcript
GET   /api/jobs/{job_id}/transcript
```

## Transcription Pipeline

Uploads create a job and schedule background processing. The current
transcription provider is a development stub:

```env
TRANSCRIPTION_PROVIDER=stub
STUB_TRANSCRIPT_TEXT=This is a development transcript placeholder.
```

This lets the backend exercise the full job lifecycle before a real
speech-to-text provider is connected:

```text
queued -> processing -> done
```

## Error Responses

Errors use one response shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "request_id": "..."
  }
}
```

Every response also includes an `X-Request-ID` header. If the frontend shows an
error, that ID can be used later to find the same request in backend logs.

## Request Logs

The API logs each request with method, path, status code, duration, and request ID.
Example:

```text
request completed request_id=... method=GET path=/api/health status_code=200 duration_ms=1.23
```

The log level is configured with:

```env
LOG_LEVEL=INFO
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

Get transcript:

```bash
curl "http://127.0.0.1:8000/api/jobs/1/transcript"
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
