"""Identifiers.

uuid4 strings rather than ObjectId: the same values fit equally well in a JSON
file and in MongoDB's ``_id`` field, so data moves between backends by plain
copying and the frontend never notices the switch.
"""

from __future__ import annotations

from uuid import uuid4


def new_id() -> str:
    return uuid4().hex
