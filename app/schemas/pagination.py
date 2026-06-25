from pydantic import Field

from app.schemas.base import AppBaseModel


class PaginationMeta(AppBaseModel):
    total: int = Field(ge=0)
    count: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    has_next: bool
    has_previous: bool
    next_offset: int | None = Field(default=None, ge=0)
    previous_offset: int | None = Field(default=None, ge=0)
