from app.services.transcript_service import (
    analyze_transcript,
    get_transcript_metadata,
    paginate_transcript_paragraphs,
    search_transcript,
    split_transcript_paragraphs,
)


def test_get_transcript_metadata_counts_characters_and_words():
    metadata = get_transcript_metadata("One two  three")

    assert metadata == {
        "character_count": 14,
        "word_count": 3,
    }


def test_analyze_transcript_returns_frontend_summary_fields():
    analysis = analyze_transcript(
        "Alice asks about Python.\n\n"
        "Bob says Python is useful, and Alice agrees."
    )

    assert analysis["character_count"] == 70
    assert analysis["word_count"] == 12
    assert analysis["paragraph_count"] == 2
    assert analysis["estimated_reading_time_seconds"] == 4
    assert analysis["unique_word_count"] == 10
    assert analysis["top_words"][:3] == [
        {"word": "alice", "count": 2},
        {"word": "python", "count": 2},
        {"word": "asks", "count": 1},
    ]


def test_search_transcript_returns_case_insensitive_limited_matches():
    result = search_transcript(
        "Alice asks a question. Later, alice answers. Alice smiles.",
        "alice",
        limit=2,
    )

    assert result["query"] == "alice"
    assert result["total_matches"] == 3
    assert result["returned_matches"] == 2
    assert result["matches"] == [
        {
            "start_index": 0,
            "end_index": 5,
            "snippet": "Alice asks a question. Later, alice answers....",
        },
        {
            "start_index": 30,
            "end_index": 35,
            "snippet": "Alice asks a question. Later, alice answers. Alice smiles.",
        },
    ]


def test_split_transcript_paragraphs_preserves_indexes_and_counts_words():
    paragraphs = split_transcript_paragraphs(
        "First paragraph line one.\n"
        "First paragraph line two.\n\n"
        "Second paragraph."
    )

    assert paragraphs == [
        {
            "index": 0,
            "start_index": 0,
            "end_index": 51,
            "text": "First paragraph line one.\nFirst paragraph line two.",
            "word_count": 8,
        },
        {
            "index": 1,
            "start_index": 53,
            "end_index": 70,
            "text": "Second paragraph.",
            "word_count": 2,
        },
    ]


def test_paginate_transcript_paragraphs_returns_pagination_metadata():
    result = paginate_transcript_paragraphs(
        "One.\n\nTwo.\n\nThree.",
        limit=1,
        offset=1,
    )

    assert result["total"] == 3
    assert result["count"] == 1
    assert result["limit"] == 1
    assert result["offset"] == 1
    assert result["has_next"] is True
    assert result["has_previous"] is True
    assert result["next_offset"] == 2
    assert result["previous_offset"] == 0
    assert result["items"][0]["text"] == "Two."
