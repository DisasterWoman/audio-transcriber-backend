from enum import Enum


class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"


class JobSortField(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"
    file_size_bytes = "file_size_bytes"
