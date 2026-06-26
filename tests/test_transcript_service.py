from app.services.transcript_service import (
    analyze_transcript,
    get_transcript_metadata,
    search_transcript,
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
