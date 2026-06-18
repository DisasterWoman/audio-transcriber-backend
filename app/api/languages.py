from fastapi import APIRouter

from app.schemas.language import Language
from app.services.language_service import get_supported_languages

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("/", response_model=list[Language])
def get_languages():
    return get_supported_languages()
