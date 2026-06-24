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

## Dev Commands

```bash
make dev      # run FastAPI locally
make test     # run tests
make lint     # run Ruff lint checks
make format   # format Python files
make check    # run lint checks and tests
make migrate  # apply database migrations
```

## Configuration

Settings are loaded from `.env`. Some values are validated at startup, so invalid
configuration fails early instead of breaking during a request.

Examples:

```env
APP_ENV=development
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=25
TRANSCRIPTION_PROVIDER=stub
```

## Useful Endpoints

```text
GET  /api/health
GET  /api/ready
GET  /api/upload-constraints
GET  /api/languages/

GET   /api/jobs/
GET   /api/jobs/stats
GET   /api/jobs/{job_id}
DELETE /api/jobs/{job_id}
POST  /api/jobs/
POST  /api/jobs/upload
POST  /api/jobs/{job_id}/process
POST  /api/jobs/{job_id}/retry
PATCH /api/jobs/{job_id}/status
PATCH /api/jobs/{job_id}/transcript
GET   /api/jobs/{job_id}/transcript
GET   /api/jobs/{job_id}/transcript/download
GET   /api/jobs/{job_id}/audio/download
```

## Transcription Pipeline

Uploads create a job and schedule background processing. The current
transcription provider is a development stub:

```env
AUTO_PROCESS_UPLOADS=true
TRANSCRIPTION_PROVIDER=stub
STUB_TRANSCRIPT_TEXT=This is a development transcript placeholder.
```

This lets the backend exercise the full job lifecycle before a real
speech-to-text provider is connected:

```text
queued -> processing -> done
```

If processing fails, the job becomes `failed` and can be retried:

```text
failed -> queued -> processing -> done
```

Each processing run increments `processing_attempts`. This makes failures easier
to debug later because the API can show whether a job failed once or many times.

You can disable automatic processing per upload by sending:

```text
auto_process=false
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
curl "http://127.0.0.1:8000/api/jobs/?language=en&limit=10&search=interview&created_from=2026-06-01T00:00:00Z"
```

Get transcript:

```bash
curl "http://127.0.0.1:8000/api/jobs/1/transcript"
```

Download transcript as text:

```bash
curl -OJ "http://127.0.0.1:8000/api/jobs/1/transcript/download"
```

Download original audio:

```bash
curl -OJ "http://127.0.0.1:8000/api/jobs/1/audio/download"
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

## Tests

The test suite currently covers service-level job rules and API response contracts.

Run the test suite:

```bash
.venv/bin/pytest
```

## CI

GitHub Actions runs lint checks and tests on pull requests and pushes to `main`.
The workflow lives in:

```text
.github/workflows/ci.yml
```
