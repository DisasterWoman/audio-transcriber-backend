from enum import Enum

from pydantic import BaseModel


class LanguageCode(str, Enum):
    ru = "ru"
    en = "en"
    tr = "tr"
    es = "es"
    fr = "fr"


class Language(BaseModel):
    code: LanguageCode
    name: str
