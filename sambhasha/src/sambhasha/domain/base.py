"""Common model settings: immutable, and unknown fields are errors rather than ignored."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DomainModel(BaseModel):
    """Base for every domain object: frozen (invariant I7 in spirit) and strict about fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")
