"""OFD container access (ZIP 6.2.0 per §6).

The package has exactly one fixed-named ``OFD.xml`` at its root. Every other
path inside the package is an ST_Loc (§7.3): case-sensitive, ``/`` = package
root, ``.`` = current, ``..`` = parent. Real producers mix absolute locs
(``/Doc_0/Signs/Signatures.xml``) and relative locs
(``Doc_0/Document.xml``), so resolution tracks the *referencing file's*
directory.
"""

from __future__ import annotations

import os
import zipfile
import tempfile
import xml.etree.ElementTree as ET
from . import ns


def _safe_extract(zf: zipfile.ZipFile, dest: str):
    """Extract a ZIP, refusing entries that would escape ``dest``.

    CPython's ``extractall`` already strips absolute paths and ``..`` segments,
    but we verify every member explicitly so a hostile package can never write
    outside the temp dir (zip-slip).
    """
    dest_root = os.path.realpath(dest)
    for member in zf.infolist():
        target = os.path.realpath(os.path.join(dest_root, member.filename))
        if target != dest_root and not target.startswith(dest_root + os.sep):
            raise ValueError("unsafe entry in OFD package: %r" % member.filename)
    zf.extractall(dest)


class OFDContainer:
    """Opens a ``.ofd`` package (or an already-extracted directory).

    All paths returned by :meth:`resolve` are absolute on disk (inside a temp
    dir for ``.ofd`` inputs) so callers can just ``open()`` them.
    """

    def __init__(self, source: str):
        self._tmp = None
        self.root = None
        if os.path.isfile(source) and source.lower().endswith(".ofd"):
            self._tmp = tempfile.mkdtemp(prefix="ofdreader_")
            with zipfile.ZipFile(source) as z:
                _safe_extract(z, self._tmp)
            self.root = self._tmp
            self.source = source
        elif os.path.isdir(source):
            self.root = os.path.abspath(source)
            self.source = source
        else:
            raise ValueError("source must be a .ofd file or an extracted directory: %r" % source)

    # -- path resolution ----------------------------------------------------

    def resolve(self, loc: str, base_dir: str | None = None) -> str:
        """Resolve an ST_Loc to an absolute on-disk path.

        ``base_dir`` is a directory (relative to the package root) that the
        *referencing* file lives in. Absolute locs (starting with ``/``) ignore
        it and resolve against the package root.

        Implementation note: we deliberately use ``os.path.join`` + ``normpath``
        rather than splitting on the OS separator, because on Windows the drive
        letter (``C:``) would otherwise be treated as a drive-relative prefix and
        corrupt the path.
        """
        if loc is None:
            raise ValueError("empty ST_Loc")
        loc = loc.strip().replace("\\", "/")
        if loc.startswith("/"):
            base = self.root
            rel = loc[1:]
        else:
            # base_dir is *always* package-relative, but callers often derive it
            # from a loc like "/Doc_0/Signs/Signature.xml", leaving a leading
            # "/". os.path.join would treat that as an absolute path and discard
            # the package root, so strip it.
            if base_dir:
                base_dir = base_dir.replace("\\", "/").lstrip("/")
            base = self.root if not base_dir else os.path.join(self.root, base_dir)
            rel = loc
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        path = os.path.join(base, *parts)
        return os.path.normpath(path)

    def exists(self, path: str) -> bool:
        return os.path.isfile(path)

    def read_file(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    def read_xml(self, loc: str, base_dir: str | None = None) -> ET.Element:
        # If an absolute path is passed (e.g. from ofd_xml_path), open directly
        # rather than re-resolving it against the package root.
        path = loc if os.path.isabs(loc) else self.resolve(loc, base_dir)
        with open(path, "rb") as f:
            return ET.fromstring(f.read())

    def list_names(self):
        """Yield every file path relative to the package root."""
        out = []
        for dirpath, _dirs, files in os.walk(self.root):
            for fn in files:
                full = os.path.join(dirpath, fn)
                out.append(os.path.relpath(full, self.root))
        return sorted(out)

    def ofd_xml_path(self) -> str | None:
        """Locate the unique ``OFD.xml`` (search root then one level deep)."""
        cand = self.resolve("OFD.xml")
        if self.exists(cand):
            return cand
        # be lenient: scan for any OFD.xml
        for name in self.list_names():
            if os.path.basename(name) == "OFD.xml":
                return self.resolve(name)
        return None

    def close(self):
        if self._tmp and os.path.isdir(self._tmp):
            import shutil

            shutil.rmtree(self._tmp, ignore_errors=True)
            self._tmp = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
