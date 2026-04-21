from fastapi import FastAPI
from app.api.routes import router as main_router
from app.api.jobs import router as jobs_router
from app.core.settings import settings

app = FastAPI(title=settings.app_name)

app.include_router(main_router)
app.include_router(jobs_router)