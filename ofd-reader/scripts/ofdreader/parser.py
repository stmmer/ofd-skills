"""Top-level OFD parser (§7.4-§7.7).

Loads the fixed ``OFD.xml`` entry, follows ``DocBody -> DocRoot`` to the
document root (Document.xml), then walks the page tree (pre-order) to discover
each page's Content.xml. Builds a :class:`OFDDocument` plus a
:class:`ResourceRegistry`.
"""

from __future__ import annotations

import os
from . import ns, container, resources
from .model import (
    OFDDocument, DocInfo, PageInfo, OutlineItem,
    ActionInfo, AnnotationInfo, SignatureInfo, SignedRef,
)


class OFDParser:
    def __init__(self, cont: "container.OFDContainer"):
        self.cont = cont
        self.doc = OFDDocument()
        self.registry = resources.ResourceRegistry()
        # TemplatePage definitions from CommonData (§7.7): id -> {loc, base_dir,
        # zorder, name}. A page references them via <Template TemplateID=.../>,
        # and they carry headers/footers/red-headers that would otherwise be
        # missing if we only read the page's own Content.xml.
        self._template_pages: dict = {}

    # -- public -------------------------------------------------------------

    def parse(self) -> OFDDocument:
        ofd_path = self.cont.ofd_xml_path()
        if not ofd_path:
            raise ValueError("no OFD.xml found in package (invalid OFD)")
        root = self.cont.read_xml(ofd_path)
        if not ns.is_el(root, "OFD"):
            raise ValueError("root element is <%s>, expected <OFD>" % ns.local(root.tag))

        self.doc.version = ns.attr(root, "Version")
        self.doc.doc_type = ns.attr(root, "DocType")

        body = ns.child(root, "DocBody")
        if body is None:
            raise ValueError("OFD.xml missing <DocBody>")

        self._parse_doc_info(ns.child(body, "DocInfo"))
        docroot_loc = ns.text_of(ns.child(body, "DocRoot")).strip()
        if not docroot_loc:
            raise ValueError("DocBody missing <DocRoot>")

        doc_root = self.cont.read_xml(docroot_loc)  # relative to package root
        if not ns.is_el(doc_root, "Document"):
            raise ValueError("DocRoot did not resolve to a <Document> element")

        self._parse_common_data(ns.child(doc_root, "CommonData"), base_dir=_dir_of(docroot_loc))
        self._parse_pages(ns.child(doc_root, "Pages"), base_dir=_dir_of(docroot_loc))
        self._parse_permissions(ns.child(doc_root, "Permissions"))
        self._parse_outlines(ns.child(doc_root, "Outlines"))
        # §18 signatures hang off DocBody (OFD.xml), not the document root.
        self._parse_signatures(body)
        # §15 annotations + §14 document-level actions hang off the document root.
        self._parse_annotations(doc_root, base_dir=_dir_of(docroot_loc))
        self._parse_doc_actions(doc_root)

        # Resource scope: document + public (page-scope added per-page if needed).
        # PublicRes/DocumentRes in CommonData are ST_Loc relative to the document
        # directory (Doc_0), so prefix them with the document base dir.
        doc_dir = _dir_of(docroot_loc)
        res_paths = []
        for r in (self._document_res, self._public_res):
            if r:
                res_paths.append(os.path.join(doc_dir, r))
        if res_paths:
            self.registry.load(self.cont, res_paths)

        return self.doc

    # -- internals ----------------------------------------------------------

    def _parse_doc_info(self, el):
        if el is None:
            return
        info = self.doc.doc_info
        mapping = {
            "Title": "title", "Author": "author", "Subject": "subject",
            "Creator": "creator", "CreationDate": "creation_date",
            "ModDate": "mod_date", "DocID": "doc_id",
        }
        for c in el:
            ln = ns.local(c.tag)
            if ln in mapping:
                setattr(info, mapping[ln], (c.text or "").strip())
            elif ln == "CustomDatas":
                for cd in ns.children(c, "CustomData"):
                    name = ns.attr(cd, "Name")
                    if name:
                        info.custom[name] = (cd.text or "").strip()

    def _parse_common_data(self, el, base_dir: str):
        if el is None:
            return
        self.doc.max_unit_id = _int(ns.text_of(ns.child(el, "MaxUnitID")))
        box = ns.child(el, "PageArea")
        if box is not None:
            self.doc.page_area = ns.parse_box(ns.text_of(ns.child(box, "PhysicalBox")))
        self._public_res = _strip(ns.text_of(ns.child(el, "PublicRes")))
        self._document_res = _strip(ns.text_of(ns.child(el, "DocumentRes")))
        # §7.7 template pages (ID + BaseLoc + ZOrder + Name).
        for tp in ns.children(el, "TemplatePage"):
            tid = _strip(ns.attr(tp, "ID"))
            tloc = _strip(ns.attr(tp, "BaseLoc"))
            if not tid or not tloc:
                continue
            self._template_pages[tid] = {
                "loc": tloc,
                "base_dir": base_dir,
                "zorder": _strip(ns.attr(tp, "ZOrder")) or "Background",
                "name": _strip(ns.attr(tp, "Name")),
            }

    def _parse_pages(self, el, base_dir: str):
        if el is None:
            return
        idx = 0
        for p in ns.children(el, "Page"):
            idx += 1
            # NOTE: per §7.6 BaseLoc and ID are *attributes* of <Page>, not
            # child elements. The standard presents them in a flat
            # "name/type/description" table (表11) alongside the Page row,
            # which reads like a parent/child tree; Appendix A's XSD is
            # explicit (<xs:attribute name="ID|BaseLoc">). Real files agree.
            base = _strip(ns.attr(p, "BaseLoc"))
            if not base:
                continue
            self.doc.pages.append(PageInfo(
                index=idx,
                unit_id=_strip(ns.attr(p, "ID")) or str(idx),
                content_loc=base,
                content_base_dir=base_dir,
                template_id=_strip(ns.attr(p, "TemplateID")),
                physical_box=self.doc.page_area,
            ))

    def _parse_permissions(self, el):
        if el is None:
            return
        for c in el:
            ln = ns.local(c.tag)
            self.doc.permissions[ln] = (c.text or "").strip() or dict(c.attrib)

    def _parse_outlines(self, el):
        if el is None:
            return
        for o in ns.children(el, "OutlineElem"):
            # Title is an *attribute* of <OutlineElem> (not a child element).
            title = _strip(ns.attr(o, "Title")) or _strip(ns.text_of(ns.child(o, "Title"))) or ""
            item = OutlineItem(title=title)
            actions = ns.child(o, "Actions")
            if actions is not None:
                action = ns.child(actions, "Action")
                if action is not None:
                    goto = ns.child(action, "Goto")
                    if goto is not None:
                        dest = ns.child(goto, "Dest")
                        if dest is not None:
                            item.page_id = _strip(ns.attr(dest, "PageID"))
                            item.dest = dict(dest.attrib)
            self.doc.outlines.append(item)

    # -- §14 actions --------------------------------------------------------

    def _parse_doc_actions(self, doc_root):
        """Document-root level actions, e.g. a DocOpen event (§14)."""
        self.doc.actions.extend(_actions_of(doc_root, context="Document"))

    # -- §15 annotations ----------------------------------------------------

    def _parse_annotations(self, doc_root, base_dir: str):
        """Two-level annotations (§15): entry file -> per-page annotation file.

        ``Document/Annotations`` is an ST_Loc to the entry file
        (Annotations.xml), which maps each page to its own annotation file.
        """
        loc = _strip(ns.text_of(ns.child(doc_root, "Annotations")))
        if not loc:
            return
        entry = self._try_read(loc, base_dir)
        if entry is None:
            return
        # Per-page FileLoc is relative to the entry file's own directory.
        ann_dir = _ref_dir(loc, base_dir)
        for page_el in ns.children(entry, "Page"):
            page_id = _strip(ns.attr(page_el, "PageID"))
            file_loc = _strip(ns.text_of(ns.child(page_el, "FileLoc")))
            if not file_loc:
                continue
            per_page = self._try_read(file_loc, ann_dir)
            if per_page is None:
                continue
            for annot in ns.children(per_page, "Annot"):
                self.doc.annotations.append(self._parse_annot(annot, page_id))

    def _parse_annot(self, annot, page_id):
        info = AnnotationInfo(page_id=page_id)
        info.annot_id = _strip(ns.attr(annot, "ID"))
        info.type = _strip(ns.attr(annot, "Type"))
        info.creator = _strip(ns.attr(annot, "Creator"))
        info.last_mod = _strip(ns.attr(annot, "LastModDate"))
        info.visible = _strip(ns.attr(annot, "Visible"))
        info.remark = _strip(ns.text_of(ns.child(annot, "Remark")))
        app = ns.child(annot, "Appearance")
        if app is not None:
            info.boundary = ns.parse_box(ns.attr(app, "Boundary"))
        info.actions = _actions_of(annot, context="Annotation")
        return info

    # -- §18 signatures -----------------------------------------------------

    def _parse_signatures(self, body):
        """Signatures list (§18): DocBody/Signatures -> Signatures.xml."""
        loc = _strip(ns.text_of(ns.child(body, "Signatures")))
        if not loc:
            return
        root = self._try_read(loc, None)
        if root is None:
            return
        self.doc.max_sign_id = _int(_strip(ns.text_of(ns.child(root, "MaxSignId"))))
        # Each Signature/@BaseLoc is relative to Signatures.xml's directory.
        sigs_dir = _ref_dir(loc, None)
        for s in ns.children(root, "Signature"):
            sid = _strip(ns.attr(s, "ID"))
            stype = _strip(ns.attr(s, "Type")) or "Seal"
            base = _strip(ns.attr(s, "BaseLoc"))
            if not base:
                continue
            sig_loc = os.path.join(sigs_dir, base)
            info = self._parse_signature_file(sid, stype, sig_loc)
            if info is not None:
                self.doc.signatures.append(info)

    def _parse_signature_file(self, sid, stype, sig_loc: str):
        root = self._try_read(sig_loc, None)
        if root is None:
            return None
        info = SignatureInfo(sign_id=sid, type=stype)
        info.signature_loc = self.cont.resolve(sig_loc, None) if not os.path.isabs(sig_loc) else sig_loc

        si = ns.child(root, "SignedInfo")
        if si is not None:
            prov = ns.child(si, "Provider")
            if prov is not None:
                info.provider_name = _strip(ns.attr(prov, "ProviderName"))
                info.provider_version = _strip(ns.attr(prov, "Version"))
                info.provider_company = _strip(ns.attr(prov, "Company"))
            info.signature_datetime = _strip(ns.text_of(ns.child(si, "SignatureDateTime")))
            info.signature_method = _strip(ns.text_of(ns.child(si, "SignatureMethod")))

            refs = ns.child(si, "References")
            if refs is not None:
                info.check_method = _strip(ns.attr(refs, "CheckMethod"))
                for r in ns.children(refs, "Reference"):
                    info.references.append(SignedRef(
                        file_ref=_strip(ns.attr(r, "FileRef")),
                        check_value=_strip(ns.text_of(ns.child(r, "CheckValue"))),
                    ))

            for sa in ns.children(si, "StampAnnot"):
                info.stamp_annot = {
                    "id": _strip(ns.attr(sa, "ID")),
                    "page_ref": _strip(ns.attr(sa, "PageRef")),
                    "boundary": ns.parse_box(ns.attr(sa, "Boundary")),
                }
            seal = ns.child(si, "Seal")
            if seal is not None:
                info.seal_loc = _strip(ns.text_of(ns.child(seal, "BaseLoc")))

        # SignedValue is a sibling loc of Signature.xml (spec: SignedValue.dat).
        sv = ns.child(root, "SignedValue")
        if sv is not None:
            sv_loc = _strip(ns.text_of(sv))
            if sv_loc:
                info.signed_value_path = self.cont.resolve(sv_loc, base_dir=os.path.dirname(sig_loc))
        return info

    # -- per-page content element ------------------------------------------

    def load_page_content(self, page: PageInfo):
        """Return the parsed Content.xml Element for a page (or None)."""
        try:
            return self.cont.read_xml(page.content_loc, base_dir=page.content_base_dir)
        except (FileNotFoundError, ETParseErr()):
            return None

    def load_page_content_expanded(self, page: PageInfo) -> list:
        """Return the ordered list of content roots to draw for a page.

        Template pages (§7.7) hold repeated content — red headers, page
        headers/footers, watermarks. Reading only the page's own Content.xml
        silently drops them, so we expand: background templates first, then the
        page content, then foreground templates. Nested template references are
        expanded recursively with cycle detection.
        """
        page_root = self.load_page_content(page)
        roots: list = []
        visited: set = set()
        self._collect_templates(page_root, roots, visited, "Background")
        if page_root is not None:
            roots.append(page_root)
        self._collect_templates(page_root, roots, visited, "Foreground")
        return roots

    def _collect_templates(self, page_root, roots, visited, zorder):
        if page_root is None:
            return
        for tpl in ns.children(page_root, "Template"):
            tid = _strip(ns.attr(tpl, "TemplateID"))
            if not tid or tid in visited:
                continue
            # ZOrder defaults to Background when omitted.
            if (_strip(ns.attr(tpl, "ZOrder")) or "Background") != zorder:
                continue
            visited.add(tid)
            tpl_root = self._load_template(tid)
            if tpl_root is None:
                continue
            # Expand the template's own (nested) templates first so background
            # layers are drawn underneath the template's content.
            self._collect_templates(tpl_root, roots, visited, zorder)
            roots.append(tpl_root)

    def _load_template(self, tid: str):
        tpl = self._template_pages.get(tid)
        if not tpl:
            return None
        return self._try_read(tpl["loc"], tpl["base_dir"])

    def _try_read(self, loc: str, base_dir):
        """Read an XML file, returning None instead of raising."""
        try:
            return self.cont.read_xml(loc, base_dir=base_dir)
        except (FileNotFoundError, OSError, ETParseErr()):
            return None


def parse_action(action_el, context: str | None = None) -> ActionInfo:
    """Parse one ``<Action>`` (§14) into an :class:`ActionInfo`.

    The behaviour is carried by a single child element: Goto / URI / GotoA /
    Sound / Movie. ``Region`` (when present) is ignored — we only surface the
    target, which is what link extraction needs.
    """
    info = ActionInfo(event=_strip(ns.attr(action_el, "Event")), context=context)

    goto = ns.child(action_el, "Goto")
    if goto is not None:
        info.kind = "Goto"
        dest = ns.child(goto, "Dest")
        if dest is not None:
            info.dest = {
                "type": _strip(ns.attr(dest, "Type")),
                "page_id": _strip(ns.attr(dest, "PageID")),
                "left": ns.attr(dest, "Left"),
                "top": ns.attr(dest, "Top"),
                "right": ns.attr(dest, "Right"),
                "bottom": ns.attr(dest, "Bottom"),
                "zoom": ns.attr(dest, "Zoom"),
            }
        else:
            bm = ns.child(goto, "Bookmark")
            if bm is not None:
                info.bookmark = _strip(ns.attr(bm, "Name"))
        return info

    uri = ns.child(action_el, "URI")
    if uri is not None:
        info.kind = "URI"
        info.uri = _strip(ns.attr(uri, "URI"))
        info.uri_base = _strip(ns.attr(uri, "Base"))
        info.uri_target = _strip(ns.attr(uri, "Target"))
        return info

    for kind in ("GotoA", "Sound", "Movie"):
        el = ns.child(action_el, kind)
        if el is not None:
            info.kind = kind
            info.attrs = dict(el.attrib)
            return info

    return info


def _actions_of(container_el, context: str) -> list:
    """Collect every ``Actions/Action`` under ``container_el`` (§14)."""
    out = []
    actions = ns.child(container_el, "Actions")
    if actions is None:
        return out
    for a in ns.children(actions, "Action"):
        out.append(parse_action(a, context=context))
    return out


def _dir_of(loc: str) -> str:
    import os

    return os.path.dirname(loc)


def _ref_dir(loc: str, base_dir: str | None) -> str:
    """Package-relative directory of the file an ST_Loc points at.

    Used to resolve *nested* locs (a Signature's BaseLoc, an annotation's
    FileLoc) which are relative to the file that declared them — not to the
    package root. ``loc`` may itself be an absolute loc (``/Doc_0/...``), in
    which case its directory is already package-rooted.
    """
    import os

    if loc.startswith("/"):
        return os.path.dirname(loc[1:])
    return os.path.dirname(os.path.join(base_dir or "", loc))


def _strip(v) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


def _int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def ETParseErr():
    import xml.etree.ElementTree as ET

    return ET.ParseError
