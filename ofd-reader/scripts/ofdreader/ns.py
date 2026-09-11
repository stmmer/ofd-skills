"""Namespace-agnostic helpers for parsing OFD XML.

OFD (GB/T 33190-2016) mandates the namespace
``http://www.ofdspec.org/2016``, but real-world producers (WPS / 点聚 / 数科)
regularly emit it with the ``ofd:`` prefix, no prefix, or subtle variations.
To stay lenient we match elements by *local name* only and never depend on a
prefix being present.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

OFD_NS = "http://www.ofdspec.org/2016"

# ---------------------------------------------------------------------------
# Element / attribute helpers (local-name based, prefix-agnostic)
# ---------------------------------------------------------------------------


def local(tag) -> str:
    """Return the local name of an ElementTree tag (strips any ``{ns}``)."""
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def is_el(elem, name: str) -> bool:
    return elem is not None and local(elem.tag) == name


def child(elem, name: str):
    """First direct child whose local name == name (or None)."""
    if elem is None:
        return None
    for c in elem:
        if is_el(c, name):
            return c
    return None


def children(elem, name: str):
    """All direct children whose local name == name."""
    if elem is None:
        return []
    return [c for c in elem if is_el(c, name)]


def attr(elem, name: str, default=None):
    if elem is None:
        return default
    return elem.get(name, default)


def text_of(elem, default: str = "") -> str:
    if elem is None or elem.text is None:
        return default
    return elem.text


# ---------------------------------------------------------------------------
# §7.3 base-type parsers
# ---------------------------------------------------------------------------


def parse_box(value: str | None):
    """ST_Box = ``x y w h`` (w, h > 0). Returns (x, y, w, h) or None."""
    if not value:
        return None
    parts = value.split()
    if len(parts) != 4:
        return None
    try:
        x, y, w, h = (float(p) for p in parts)
    except ValueError:
        return None
    return x, y, w, h


def parse_array(value: str | None):
    """ST_Array = whitespace separated scalars (non-nestable)."""
    if not value:
        return []
    out = []
    for p in value.split():
        try:
            out.append(float(p))
        except ValueError:
            # keep non-numeric tokens (e.g. DeltaX "g" directives) as-is
            out.append(p)
    return out


def parse_pos(value: str | None):
    """ST_Pos = ``x y``."""
    if not value:
        return None
    parts = value.split()
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def read_xml(bytes_data: bytes) -> ET.Element:
    """Parse XML bytes into an Element, lenient about the namespace."""
    return ET.fromstring(bytes_data)
