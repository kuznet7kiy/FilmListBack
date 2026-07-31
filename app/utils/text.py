"""Text normalization for search and sorting."""

from __future__ import annotations


def normalize_title(title: str) -> str:
    """Reduce a title to a comparable form.

    Case is folded away and surrounding whitespace is trimmed, so that search
    and alphabetical ordering behave identically on the JSON and Mongo backends.
    """
    return title.casefold().strip()
