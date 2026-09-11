"""Plain data objects produced by the parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocInfo:
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    creation_date: Optional[str] = None
    mod_date: Optional[str] = None
    doc_id: Optional[str] = None
    custom: dict = field(default_factory=dict)


@dataclass
class PageInfo:
    index: int
    unit_id: str
    content_loc: str          # ST_Loc of the page Content.xml
    content_base_dir: str     # dir (rel to root) the loc is resolved against
    template_id: Optional[str] = None
    physical_box: Optional[tuple] = None


@dataclass
class OutlineItem:
    title: str
    page_id: Optional[str] = None
    dest: Optional[dict] = None


@dataclass
class MediaInfo:
    rel_path: str             # absolute on-disk path to the resource bytes
    type: Optional[str] = None
    fmt: Optional[str] = None


@dataclass
class FontInfo:
    name: Optional[str] = None
    rel_path: Optional[str] = None


@dataclass
class ActionInfo:
    """An interactive action (§14): Goto / URI / GotoA / Sound / Movie.

    ``context`` records where the action was found (Document root, an outline
    node, a page-content object, or an annotation) so callers can route it.
    """
    event: Optional[str] = None
    kind: Optional[str] = None          # Goto | URI | GotoA | Sound | Movie
    context: Optional[str] = None
    dest: Optional[dict] = None         # Goto -> CT_Dest attributes
    bookmark: Optional[str] = None      # Goto -> Bookmark Name
    uri: Optional[str] = None           # URI
    uri_base: Optional[str] = None
    uri_target: Optional[str] = None
    attrs: dict = field(default_factory=dict)  # GotoA/Sound/Movie raw attributes


@dataclass
class AnnotationInfo:
    """A page annotation (§15)."""
    page_id: Optional[str] = None
    annot_id: Optional[str] = None
    type: Optional[str] = None          # Link | Path | Highlight | Stamp | Watermark
    creator: Optional[str] = None
    last_mod: Optional[str] = None
    visible: Optional[str] = None
    boundary: Optional[tuple] = None     # Appearance/@Boundary
    remark: Optional[str] = None
    actions: list = field(default_factory=list)   # list[ActionInfo]


@dataclass
class SignedRef:
    """One file covered by a signature (§18.2.1)."""
    file_ref: Optional[str] = None       # ST_Loc relative to the Signature.xml dir
    check_value: Optional[str] = None     # base64 digest


@dataclass
class SignatureInfo:
    """A digital signature (§18)."""
    sign_id: Optional[str] = None
    type: Optional[str] = None           # Seal | Sign
    provider_name: Optional[str] = None
    provider_version: Optional[str] = None
    provider_company: Optional[str] = None
    signature_method: Optional[str] = None
    signature_datetime: Optional[str] = None
    check_method: Optional[str] = None
    references: list = field(default_factory=list)   # list[SignedRef]
    stamp_annot: Optional[dict] = None    # {id, page_ref, boundary}
    seal_loc: Optional[str] = None        # Seal/BaseLoc (relative to Signature.xml dir)
    signed_value_path: Optional[str] = None   # absolute path to SignValue.dat
    signature_loc: Optional[str] = None  # absolute path to Signature.xml


@dataclass
class OFDDocument:
    version: Optional[str] = None
    doc_type: Optional[str] = None
    doc_info: DocInfo = field(default_factory=DocInfo)
    pages: list = field(default_factory=list)
    outlines: list = field(default_factory=list)
    permissions: dict = field(default_factory=dict)
    page_area: Optional[tuple] = None
    max_unit_id: Optional[int] = None
    # -- extensions added for the rich-extraction feature set --
    signatures: list = field(default_factory=list)   # list[SignatureInfo]  (§18)
    annotations: list = field(default_factory=list)   # list[AnnotationInfo] (§15)
    actions: list = field(default_factory=list)        # document-level actions (§14)
    max_sign_id: Optional[int] = None
