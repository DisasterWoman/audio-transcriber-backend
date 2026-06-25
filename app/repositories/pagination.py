def build_paginated_response(
    items: list,
    total: int,
    limit: int,
    offset: int,
) -> dict:
    count = len(items)
    next_offset = offset + limit
    previous_offset = max(offset - limit, 0)

    has_next = next_offset < total
    has_previous = offset > 0 and total > 0

    return {
        "items": items,
        "total": total,
        "count": count,
        "limit": limit,
        "offset": offset,
        "has_next": has_next,
        "has_previous": has_previous,
        "next_offset": next_offset if has_next else None,
        "previous_offset": previous_offset if has_previous else None,
    }
