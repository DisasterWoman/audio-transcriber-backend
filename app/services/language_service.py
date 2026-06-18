from app.schemas.language import LanguageCode


LANGUAGE_NAMES = {
    LanguageCode.ru: "Russian",
    LanguageCode.en: "English",
    LanguageCode.tr: "Turkish",
    LanguageCode.es: "Spanish",
    LanguageCode.fr: "French",
}


def get_supported_languages():
    return [
        {
            "code": language,
            "name": LANGUAGE_NAMES[language],
        }
        for language in LanguageCode
    ]
