"""Resource registry with the three-level scope fallback (§7.9).

A resource (font / color space / draw param / image / multimedia) is looked up
*from the inside out*: Page scope (PageRes) -> Document scope (DocumentRes) ->
Public scope (PublicRes). Each Res file carries a ``BaseLoc`` that anchors the
relative ``Loc`` of the actual bytes inside the package.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

from . import ns, container
from .model import MediaInfo, FontInfo


class ResourceRegistry:
    def __init__(self):
        # order matters: later scopes are fallbacks, so we store in lookup order
        self._media: dict[str, MediaInfo] = {}
        self._fonts: dict[str, FontInfo] = {}
        self._composites: dict[str, "ET.Element"] = {}
        self._loaded: list[str] = []

    def load(self, cont: "container.OFDContainer", res_rel_paths: list[str]):
        """Load one or more Res XML files.

        ``res_rel_paths`` are package-relative paths (e.g. ``Doc_0/DocumentRes.xml``).
        Pass them inside-out: page res first, then document, then public — but
        because we key by ID and never overwrite an existing ID, the *first*
        (innermost) definition wins, which is exactly the spec's rule.
        """
        for rel in res_rel_paths:
            if rel in self._loaded:
                continue
            self._loaded.append(rel)
            try:
                root = cont.read_xml(rel)
            except (FileNotFoundError, ET.ParseError):
                continue
            res_dir = os.path.dirname(rel)
            base_loc = ns.attr(root, "BaseLoc") or ""
            media_base = os.path.join(res_dir, base_loc) if base_loc else res_dir

            for mm in ns.children(root, "MultiMedias"):
                for m in ns.children(mm, "MultiMedia"):
                    mid = ns.attr(m, "ID")
                    if mid is None:
                        continue
                    media_node = _first_child(m, ("MediaFile", "Loc"))
                    loc = (media_node.text or "").strip() if media_node is not None else ""
                    fmt = ns.attr(m, "Format") or ns.attr(m, "Type")
                    path = cont.resolve(loc, base_dir=media_base) if loc else None
                    self._media.setdefault(mid, MediaInfo(path, ns.attr(m, "Type"), fmt))

            for fnts in ns.children(root, "Fonts"):
                for f in ns.children(fnts, "Font"):
                    fid = ns.attr(f, "ID")
                    if fid is None:
                        continue
                    ff = _first_child(f, ("FontFile", "Loc"))
                    loc = (ff.text or "").strip() if ff is not None else ""
                    fp = cont.resolve(loc, base_dir=media_base) if loc else None
                    self._fonts.setdefault(fid, FontInfo(ns.attr(f, "FontName"), fp))

            # Composite graphic units (§13): a reusable group of page elements.
            # We keep the inner <Content> (a CT_PageBlock) so extract.py can
            # expand a CompositeObject's ResourceID into its real TextObject /
            # ImageObject children.
            for cgus in ns.children(root, "CompositeGraphicUnits"):
                for cgu in ns.children(cgus, "CompositeGraphicUnit"):
                    cid = ns.attr(cgu, "ID")
                    if cid is None:
                        continue
                    self._composites.setdefault(cid, ns.child(cgu, "Content"))

    def resolve_media(self, ref_id: str) -> MediaInfo | None:
        return self._media.get(ref_id)

    def resolve_font(self, ref_id: str) -> FontInfo | None:
        return self._fonts.get(ref_id)

    def resolve_composite(self, ref_id: str):
        """Return the inner CT_PageBlock Element of a composite unit, or None."""
        return self._composites.get(ref_id)

    def media_ids(self):
        return list(self._media.keys())

    def font_ids(self):
        return list(self._fonts.keys())


def _first_child(elem, names):
    """First direct child of ``elem`` whose local name is in ``names`` (or None).

    We avoid ``ns.child`` here: in some real-world parse contexts its iterator
    based lookup proved unreliable, whereas a plain local-name scan is robust.
    """
    if elem is None:
        return None
    for c in elem:
        if ns.local(c.tag) in names:
            return c
    return None
