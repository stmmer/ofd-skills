"""Content extraction: text (reading-order aware) and embedded images (§9-§11).

Text positioning in OFD is done either per-glyph (``TextCode`` carries X/Y
arrays) or per-run (whole string at one point via Body+Delta). We collect every
glyph with its page-space coordinate, cluster glyphs into lines by Y, then order
each line left-to-right and insert a space only when the horizontal gap between
consecutive glyphs exceeds a threshold. This reproduces natural reading order
for both the per-glyph producers (WPS/点聚) and looser layouts.
"""

from __future__ import annotations

import os
import re
from . import ns
from .resources import ResourceRegistry
from .parser import parse_action

# After gap-based spacing, OFD producers (WPS/点聚) sometimes split a run such
# as "2004" into two TextObjects with a visible gap, which would wrongly insert
# a space. We strip a space that sits *after a digit* and *before a CJK char /
# digit / date unit*, reproducing the natural reading "2004年 8月 28日" while
# keeping intentional inter-token spaces like "— 1 —" or "公开 ★ 1年".
_DIGIT_ADJACENT_SPACE = re.compile(r"(?<=\d)\s+(?=[\u4e00-\u9fff\d年月份日号次会时分秒])")
# Strip a space that sits directly inside full-width brackets, e.g. "（三 ）" -> "（三）".
_PAREN_SPACE = re.compile(r"(?<=[（])\s+|\s+(?=[）])")

# Tuning (millimetres, since OFD coordinates are in mm). Page space origin is
# top-left with Y pointing down, so a larger Y == lower on the page.
LINE_THRESHOLD_MM = 2.0     # glyphs within this Y-band belong to one line
SPACE_GAP_MM = 1.5          # horizontal gap larger than this => insert a space


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------


def iter_content_objects(*content_roots, composite_reg: ResourceRegistry | None = None, _expanding=None):
    """Yield TextObject / ImageObject elements anywhere under Content.

    Accepts any number of content roots, because a page is drawn as
    **template layers + its own content** (§7.7) — pass them in draw order and
    the caller sees one flat stream.

    CompositeObjects (§13) carry only a ``ResourceID`` pointing at a
    ``CompositeGraphicUnit`` defined in the resources, so the text and images
    inside them would be invisible to a naive scan. When ``composite_reg`` is
    supplied we resolve and expand them; unresolved ones are still yielded so
    they can be reported rather than silently dropped. ``_expanding`` guards
    against a composite that (illegally) references itself.
    """
    if _expanding is None:
        _expanding = frozenset()
    for content_root in content_roots:
        if content_root is None:
            continue
        for el in content_root.iter():
            ln = ns.local(el.tag)
            if ln == "CompositeObject":
                rid = ns.attr(el, "ResourceID")
                if composite_reg is not None and rid and rid not in _expanding:
                    inner = composite_reg.resolve_composite(rid)
                    if inner is not None:
                        yield from iter_content_objects(
                            inner, composite_reg=composite_reg, _expanding=_expanding | {rid}
                        )
                        continue
                yield el
            elif ln in ("TextObject", "ImageObject"):
                yield el


def _glyphs_of(text_obj):
    box = ns.parse_box(ns.attr(text_obj, "Boundary"))
    if not box:
        return []
    x0, y0, _w, _h = box
    glyphs = []
    for tc in ns.children(text_obj, "TextCode"):
        t = (tc.text or "").replace("\n", "")
        if not t:
            continue
        xs = ns.parse_array(ns.attr(tc, "X"))
        ys = ns.parse_array(ns.attr(tc, "Y"))
        for i, ch in enumerate(t):
            cx = x0 + (xs[i] if i < len(xs) else (xs[0] if xs else 0.0))
            cy = y0 + (ys[i] if i < len(ys) else (ys[0] if ys else 0.0))
            glyphs.append((cx, cy, ch))
    return glyphs


def extract_page_text(*content_roots, composite_reg: ResourceRegistry | None = None) -> list[str]:
    """Return a list of text lines for one page, in reading order.

    Pass every layer of the page (background templates, page content,
    foreground templates) — glyphs are re-ordered by coordinate, so the merged
    stream still yields correct reading order.
    """
    glyphs = []
    for el in iter_content_objects(*content_roots, composite_reg=composite_reg):
        if ns.local(el.tag) == "TextObject":
            glyphs.extend(_glyphs_of(el))
    if not glyphs:
        return []

    glyphs.sort(key=lambda g: (round(g[1], 3), g[0]))

    lines: list[list[tuple[float, str]]] = []
    cur: list[tuple[float, str]] = []
    cur_y = None
    for cx, cy, ch in glyphs:
        if cur_y is None or abs(cy - cur_y) > LINE_THRESHOLD_MM:
            if cur:
                lines.append(cur)
            cur = [(cx, ch)]
            cur_y = cy
        else:
            cur.append((cx, ch))
    if cur:
        lines.append(cur)

    out = []
    for line in lines:
        line.sort(key=lambda g: g[0])
        s = ""
        for k, (cx, ch) in enumerate(line):
            s += ch
            if k + 1 < len(line):
                nx = line[k + 1][0]
                if nx - cx > SPACE_GAP_MM:
                    s += " "
        s = _DIGIT_ADJACENT_SPACE.sub("", s)
        s = _PAREN_SPACE.sub("", s)
        out.append(s)
    return out


def extract_document_text(pages_content, composite_reg: ResourceRegistry | None = None) -> list[list[str]]:
    """pages_content: iterable of (page_index, content_root | list-of-roots)."""
    out = []
    for _i, c in pages_content:
        roots = c if isinstance(c, (list, tuple)) else [c]
        out.append(extract_page_text(*roots, composite_reg=composite_reg))
    return out


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


def _ext_for(path: str, fmt: str | None) -> str:
    if fmt:
        f = fmt.lower()
        if f in ("png", "jpeg", "jpg", "tif", "tiff", "bmp", "gif", "webp"):
            return "jpg" if f == "jpeg" else f
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    return ext or "bin"


def extract_page_images(*content_roots, registry: ResourceRegistry, cont, out_dir: str,
                        page_index: int, composite_reg: ResourceRegistry | None = None) -> list[str]:
    """Extract every ImageObject's bytes to ``out_dir``; return saved paths.

    Takes the same multiple content roots as :func:`extract_page_text`, so
    images living on a template layer (red headers, watermarks) are captured too.
    """
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for el in iter_content_objects(*content_roots, composite_reg=composite_reg):
        if ns.local(el.tag) != "ImageObject":
            continue
        rid = ns.attr(el, "ResourceID")
        if rid is None:
            continue
        info = registry.resolve_media(rid)
        if info is None or not info.rel_path or not cont.exists(info.rel_path):
            continue
        data = cont.read_file(info.rel_path)
        ext = _ext_for(info.rel_path, info.fmt)
        fname = "page_%02d_img_%s.%s" % (page_index, rid, ext)
        dst = os.path.join(out_dir, fname)
        with open(dst, "wb") as f:
            f.write(data)
        saved.append(dst)
    return saved


# ---------------------------------------------------------------------------
# Composite objects (§13) and actions (§14)
# ---------------------------------------------------------------------------


def iter_composite_objects(*content_roots):
    """Yield every CompositeObject element (§13) found in the content."""
    for root in content_roots:
        if root is None:
            continue
        for el in root.iter():
            if ns.local(el.tag) == "CompositeObject":
                yield el


def _parent_map(root):
    """child Element -> parent Element, used to label an action's owner."""
    return {c: p for p in root.iter() for c in p}


def _owner_name(el, parents):
    """Nearest enclosing page-object name for an <Action> element."""
    cur = el
    seen = 0
    while cur in parents and seen < 64:
        cur = parents[cur]
        ln = ns.local(cur.tag)
        if ln in ("TextObject", "ImageObject", "PathObject", "CompositeObject",
                  "PageBlock", "Layer", "Page"):
            return ln
        seen += 1
    return "PageContent"


def extract_actions(*content_roots) -> list:
    """Collect every Action declared inside page content (§14).

    Actions can hang off any graphic unit (a hyperlinked text run, a clickable
    image), so we walk the whole tree and label each one with the name of the
    object that owns it.
    """
    out = []
    for root in content_roots:
        if root is None:
            continue
        parents = _parent_map(root)
        for el in root.iter():
            if ns.local(el.tag) != "Action":
                continue
            out.append(parse_action(el, context=_owner_name(el, parents)))
    return out
