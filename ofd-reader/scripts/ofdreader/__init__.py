"""ofdreader — parse GB/T 33190-2016 (OFD) fixed-layout documents.

A small, dependency-free reader: open the ZIP container, follow the
``OFD.xml -> DocBody -> DocRoot`` chain, walk the page tree, then extract text
and embedded images. Built to be lenient about real-world files (OFD v1.1,
numeric ST_ID, vendor extensions) while still validating against the
``ofd-standard`` skill's Appendix-A schemas when available.
"""

from .container import OFDContainer
from .parser import OFDParser
from .resources import ResourceRegistry
from .extract import (
    extract_page_text, extract_page_images, extract_actions, iter_composite_objects,
)
from .model import OFDDocument, ActionInfo, AnnotationInfo, SignatureInfo, SignedRef

__all__ = [
    "OFDContainer",
    "OFDParser",
    "ResourceRegistry",
    "OFDDocument",
    "ActionInfo",
    "AnnotationInfo",
    "SignatureInfo",
    "SignedRef",
    "extract_page_text",
    "extract_page_images",
    "extract_actions",
    "iter_composite_objects",
]


def open_ofd(source: str):
    """Convenience: open + parse, returns (OFDContainer, OFDDocument).

    Attachments on the returned document:
      * ``doc.registry``  — :class:`ResourceRegistry` for image/composite lookup
      * ``doc.parser``    — the :class:`OFDParser`, needed for template-page
        expansion (``load_page_content_expanded``)
    """
    cont = OFDContainer(source)
    parser = OFDParser(cont)
    doc = parser.parse()
    doc.registry = parser.registry
    doc.parser = parser
    return cont, doc
