from enum import Enum

from app.schemas.base import AppBaseModel


class LanguageCode(str, Enum):
    ru = "ru"
    en = "en"
    tr = "tr"
    es = "es"
    fr = "fr"


class Language(AppBaseModel):
    code: LanguageCode
    name: str
