from app.repositories.pagination import build_paginated_response


def test_build_paginated_response_for_middle_page():
    response = build_paginated_response(
        items=["item-3", "item-4"],
        total=5,
        limit=2,
        offset=2,
    )

    assert response == {
        "items": ["item-3", "item-4"],
        "total": 5,
        "count": 2,
        "limit": 2,
        "offset": 2,
        "has_next": True,
        "has_previous": True,
        "next_offset": 4,
        "previous_offset": 0,
    }


def test_build_paginated_response_for_last_page():
    response = build_paginated_response(
        items=["item-5"],
        total=5,
        limit=2,
        offset=4,
    )

    assert response["count"] == 1
    assert response["has_next"] is False
    assert response["has_previous"] is True
    assert response["next_offset"] is None
    assert response["previous_offset"] == 2
