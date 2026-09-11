"""Lenient structural validation + optional Appendix-A schema check.

Two layers:

1. **Built-in lenient checks** (stdlib only) — confirms the package opens, the
   unique ``OFD.xml`` exists, the namespace is right, and every page's
   ``BaseLoc`` resolves to well-formed XML. These never reject a real file just
   because it uses OFD v1.1, numeric IDs, or vendor extensions.
2. **Strict Appendix-A schema check** (optional) — if the ``ofd-standard`` skill
   is installed and ``lxml`` is available, we delegate to its bundled
   ``validate.py`` for authoritiative XSD validation of every XML in the package.
"""

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET

from . import ns, container

def _sibling_skill_validator() -> str:
    """Path to the sibling ``ofd-standard`` skill's validator.

    Derived from this file's location
    (``<skills>/ofd-reader/scripts/ofdreader/validate.py``) rather than
    hard-coded, so the skill stays portable — and never embeds a machine
    specific user directory in a published repo.
    """
    here = os.path.dirname(os.path.abspath(__file__))          # .../scripts/ofdreader
    scripts = os.path.dirname(here)                            # .../scripts
    skill_dir = os.path.dirname(scripts)                       # .../ofd-reader
    skills_root = os.path.dirname(skill_dir)                   # .../skills
    return os.path.join(skills_root, "ofd-standard", "validate.py")


# common install locations for the ofd-standard skill
_SKILL_CANDIDATES = [
    os.path.expanduser(os.path.join("~", ".workbuddy", "skills", "ofd-standard", "validate.py")),
    _sibling_skill_validator(),
]


def lenient_check(cont: "container.OFDContainer", doc) -> list[tuple[str, str]]:
    """Return list of (level, message); level in {OK, WARN, FAIL}."""
    issues = []

    def add(level, msg):
        issues.append((level, msg))

    # 1. OFD.xml present
    ofd_path = cont.ofd_xml_path()
    if not ofd_path:
        add("FAIL", "package has no OFD.xml (not a valid OFD)")
        return issues
    add("OK", "found unique OFD.xml")

    # 2. namespace
    try:
        root = cont.read_xml(ofd_path)
    except ET.ParseError as e:
        add("FAIL", "OFD.xml is not well-formed XML: %s" % e)
        return issues
    ns_uri = "{%s}" % ns.OFD_NS
    if ns_uri not in (root.tag or ""):
        add("WARN", "root tag namespace is not %s (got %s)" % (ns.OFD_NS, root.tag))
    else:
        add("OK", "namespace = %s" % ns.OFD_NS)

    # 3. version (lenient: anything is allowed, just reported)
    ver = ns.attr(root, "Version")
    add("OK", "OFD Version=%s, DocType=%s" % (ver, ns.attr(root, "DocType")))

    # 4. every page BaseLoc resolves + is well-formed
    if not doc.pages:
        add("WARN", "no pages discovered")
    for p in doc.pages:
        loc = p.content_loc
        try:
            path = cont.resolve(loc, base_dir=p.content_base_dir)
        except Exception as e:  # noqa: BLE001
            add("FAIL", "page %s: cannot resolve %s (%s)" % (p.unit_id, loc, e))
            continue
        if not cont.exists(path):
            add("FAIL", "page %s: Content.xml missing at %s" % (p.unit_id, loc))
            continue
        try:
            cont.read_xml(loc, base_dir=p.content_base_dir)
            add("OK", "page %s: %s parses OK" % (p.unit_id, loc))
        except ET.ParseError as e:
            add("FAIL", "page %s: %s not well-formed (%s)" % (p.unit_id, loc, e))

    return issues


def schema_check(target: str) -> tuple[bool, str]:
    """Run the skill's validate.py if available; return (available, output)."""
    validator = None
    for c in _SKILL_CANDIDATES:
        if os.path.isfile(c):
            validator = c
            break
    if not validator:
        return False, "ofd-standard skill validate.py not found; skipping strict schema check"

    # ensure lxml is importable
    try:
        import lxml  # noqa: F401
    except ImportError:
        return False, "lxml not installed; strict schema check skipped (pip install lxml)"

    # 必须用 sys.executable —— 裸 `python` 会走 PATH 上的另一个解释器，
    # 上面那句 `import lxml` 检查的是**当前**解释器，两者可能不是同一个，
    # 结果就是检查通过、子进程却报 ModuleNotFoundError。
    try:
        proc = subprocess.run(
            [sys.executable or "python", validator, target],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:  # noqa: BLE001
        return False, "could not run validator: %s" % e
    return True, (proc.stdout + proc.stderr).strip()
