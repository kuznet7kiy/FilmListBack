"""A single sort table shared by both storage implementations.

Key -> (field, descending?). Ties are always broken by ``title_norm``
ascending, so JSON and Mongo return the same order.
"""

from __future__ import annotations

from app.domain.queries import SortKey

TIEBREAKER = "title_norm"

SORT_SPEC: dict[SortKey, tuple[str, bool]] = {
    SortKey.TITLE_ASC: ("title_norm", False),
    SortKey.YEAR_DESC: ("year", True),
    SortKey.YEAR_ASC: ("year", False),
    SortKey.RATING_DESC: ("rating", True),
    SortKey.RATING_ASC: ("rating", False),
    SortKey.CREATED_DESC: ("created_at", True),
}
