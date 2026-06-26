from collections import Counter
from math import ceil

TRANSCRIPT_SEARCH_CONTEXT_CHARS = 40
TRANSCRIPT_READING_WORDS_PER_MINUTE = 200
TOP_WORD_LIMIT = 10
MIN_KEYWORD_LENGTH = 3
STOP_WORDS = {
    "and",
    "are",
    "but",
    "for",
    "from",
    "has",
    "have",
    "not",
    "that",
    "the",
    "this",
    "was",
    "with",
    "you",
}


def get_transcript_metadata(transcript_text: str) -> dict:
    return {
        "character_count": len(transcript_text),
        "word_count": len(get_transcript_words(transcript_text)),
    }


def analyze_transcript(transcript_text: str) -> dict:
    words = get_transcript_words(transcript_text)
    word_count = len(words)

    return {
        **get_transcript_metadata(transcript_text),
        "paragraph_count": count_transcript_paragraphs(transcript_text),
        "estimated_reading_time_seconds": estimate_reading_time_seconds(word_count),
        "unique_word_count": count_unique_words(words),
        "top_words": get_top_words(words),
    }


def search_transcript(transcript_text: str, query: str, limit: int = 10) -> dict:
    matches = find_transcript_matches(
        transcript_text,
        query,
        limit=limit,
    )

    return {
        "query": query,
        "total_matches": count_transcript_matches(transcript_text, query),
        "returned_matches": len(matches),
        "matches": matches,
    }


def get_transcript_words(transcript_text: str) -> list[str]:
    return transcript_text.split()


def count_transcript_paragraphs(transcript_text: str) -> int:
    return len(
        [
            paragraph
            for paragraph in transcript_text.splitlines()
            if paragraph.strip()
        ]
    )


def estimate_reading_time_seconds(word_count: int) -> int:
    if word_count == 0:
        return 0

    return ceil((word_count / TRANSCRIPT_READING_WORDS_PER_MINUTE) * 60)


def get_top_words(words: list[str], limit: int = TOP_WORD_LIMIT) -> list[dict]:
    normalized_words = []
    for word in words:
        normalized_word = normalize_word(word)
        if should_count_as_keyword(normalized_word):
            normalized_words.append(normalized_word)

    counts = Counter(normalized_words)

    return [
        {"word": word, "count": count}
        for word, count in counts.most_common(limit)
    ]


def count_unique_words(words: list[str]) -> int:
    normalized_words = {normalize_word(word) for word in words}
    normalized_words.discard("")
    return len(normalized_words)


def normalize_word(word: str) -> str:
    return word.casefold().strip(".,!?;:\"'()[]{}")


def should_count_as_keyword(word: str) -> bool:
    return len(word) >= MIN_KEYWORD_LENGTH and word not in STOP_WORDS


def count_transcript_matches(transcript_text: str, query: str) -> int:
    normalized_transcript = transcript_text.casefold()
    normalized_query = query.casefold()
    count = 0
    start = 0

    while True:
        match_start = normalized_transcript.find(normalized_query, start)
        if match_start == -1:
            return count

        count += 1
        start = match_start + len(normalized_query)


def find_transcript_matches(
    transcript_text: str,
    query: str,
    limit: int = 10,
) -> list[dict]:
    normalized_transcript = transcript_text.casefold()
    normalized_query = query.casefold()
    matches = []
    start = 0

    while len(matches) < limit:
        match_start = normalized_transcript.find(normalized_query, start)
        if match_start == -1:
            return matches

        match_end = match_start + len(query)
        matches.append(
            {
                "start_index": match_start,
                "end_index": match_end,
                "snippet": build_transcript_search_snippet(
                    transcript_text,
                    match_start,
                    match_end,
                ),
            }
        )
        start = match_end

    return matches


def build_transcript_search_snippet(
    transcript_text: str,
    match_start: int,
    match_end: int,
) -> str:
    snippet_start = max(match_start - TRANSCRIPT_SEARCH_CONTEXT_CHARS, 0)
    snippet_end = min(match_end + TRANSCRIPT_SEARCH_CONTEXT_CHARS, len(transcript_text))
    snippet = transcript_text[snippet_start:snippet_end].strip()
    normalized_snippet = " ".join(snippet.split())

    prefix = "..." if snippet_start > 0 else ""
    suffix = "..." if snippet_end < len(transcript_text) else ""

    return f"{prefix}{normalized_snippet}{suffix}"
