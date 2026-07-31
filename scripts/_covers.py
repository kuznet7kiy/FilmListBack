"""Generate placeholder covers for the demo data.

We have no real posters, so we draw an SVG instead: a gradient derived from
the title (a given movie always gets the same colours), the title and the year.
"""

from __future__ import annotations

from hashlib import blake2b
from xml.sax.saxutils import escape

WIDTH, HEIGHT = 400, 600

_PALETTE: tuple[tuple[str, str], ...] = (
    ("#1e3a8a", "#0f172a"),
    ("#7f1d1d", "#1c1917"),
    ("#064e3b", "#0f172a"),
    ("#4c1d95", "#1e1b4b"),
    ("#78350f", "#1c1917"),
    ("#0c4a6e", "#0f172a"),
    ("#831843", "#1e1b4b"),
    ("#334155", "#0f172a"),
)

_MAX_LINE = 16
_MAX_LINES = 4


def _wrap(title: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in title.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= _MAX_LINE or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    if len(lines) > _MAX_LINES:
        lines = lines[: _MAX_LINES - 1] + [lines[_MAX_LINES - 1][: _MAX_LINE - 1] + "…"]
    return lines


def render_cover(title: str, year: int) -> bytes:
    digest = blake2b(title.encode("utf-8"), digest_size=4).digest()
    start, end = _PALETTE[digest[0] % len(_PALETTE)]
    angle = 20 + digest[1] % 50

    lines = _wrap(title)
    line_height = 42
    first_y = HEIGHT // 2 - (len(lines) - 1) * line_height // 2
    tspans = "".join(
        f'<tspan x="{WIDTH // 2}" y="{first_y + index * line_height}">{escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="g" gradientTransform="rotate({angle})">
      <stop offset="0%" stop-color="{start}"/>
      <stop offset="100%" stop-color="{end}"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#g)"/>
  <circle cx="{WIDTH - 60}" cy="70" r="120" fill="#ffffff" opacity="0.05"/>
  <circle cx="40" cy="{HEIGHT - 40}" r="90" fill="#ffffff" opacity="0.04"/>
  <text text-anchor="middle" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="600">{tspans}</text>
  <text x="{WIDTH // 2}" y="{first_y + len(lines) * line_height + 16}" text-anchor="middle" fill="#ffffff" opacity="0.7" font-family="Segoe UI, Arial, sans-serif" font-size="24">{year}</text>
</svg>
"""
    return svg.encode("utf-8")
