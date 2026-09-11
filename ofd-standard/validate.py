#!/usr/bin/env python3
"""Validate an OFD file (.ofd) or an extracted directory against the bundled
GB/T 33190-2016 Appendix A schemas (offline, no network needed).

Requires lxml:  pip install lxml

Usage:
  python validate.py path/to/document.ofd            # validate all XML in the package
  python validate.py path/to/extracted_ofd_dir/      # validate an already-unzipped package
  python validate.py --selfcheck                     # validate the bundled schemas themselves

Each .xml is mapped to its schema by its root element name
(OFD->OFD.xsd, Document->Document.xsd, Page->Page.xsd, Res->Res.xsd, ...).
"""
import os
import sys
import glob
import zipfile
import tempfile
import argparse
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.join(HERE, "schemas")

# root element local name -> schema file (Appendix A)
ROOT_TO_SCHEMA = {
    "OFD": "OFD.xsd",
    "Document": "Document.xsd",
    "Page": "Page.xsd",
    "Res": "Res.xsd",
    "Annotations": "Annotations.xsd",
    "Annotation": "Annotation.xsd",
    "Signatures": "Signatures.xsd",
    "Signature": "Signature.xsd",
    "CustomTags": "CustomTags.xsd",
    "Extensions": "Extensions.xsd",
    "Attachments": "Attachments.xsd",
    "Version": "Version.xsd",
    "Versions": "Version.xsd",
}


def schema_for(root_local):
    return ROOT_TO_SCHEMA.get(root_local)


def iter_xml_paths(target):
    """Return (list_of_xml_paths, base_dir_for_relpath)."""
    if os.path.isfile(target) and target.lower().endswith(".ofd"):
        tmp = tempfile.mkdtemp(prefix="ofdval_")
        with zipfile.ZipFile(target) as z:
            z.extractall(tmp)
        return [p for p in sorted(
            glob.glob(os.path.join(tmp, "**", "*.xml"), recursive=True))], tmp
    if os.path.isdir(target):
        return [p for p in sorted(
            glob.glob(os.path.join(target, "**", "*.xml"), recursive=True))], target
    return [], None


def validate_xml_file(xml_path):
    try:
        tree = etree.parse(xml_path)
    except etree.XMLSyntaxError as e:
        return False, "XML parse error: %s" % e
    root = tree.getroot()
    local = etree.QName(root).localname
    sf = schema_for(local)
    if not sf:
        return None, "no schema mapped for root <%s> (skipped)" % local
    sp = os.path.join(SCHEMA_DIR, sf)
    if not os.path.exists(sp):
        return False, "schema %s missing" % sf
    try:
        schema = etree.XMLSchema(etree.parse(sp))
    except etree.XMLSchemaParseError as e:
        return False, "schema %s invalid: %s" % (sf, e)
    if schema.validate(tree):
        return True, "valid against %s" % sf
    return False, "INVALID against %s:\n%s" % (sf, schema.error_log)


def selfcheck():
    print("Self-checking bundled schemas...")
    bad = 0
    for f in sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.xsd"))):
        try:
            etree.XMLSchema(etree.parse(f))
            print("  OK  ", os.path.basename(f))
        except etree.XMLSchemaParseError as e:
            bad += 1
            print("  FAIL", os.path.basename(f), str(e).splitlines()[0])
    print("schema failures:", bad)
    return bad


def main():
    ap = argparse.ArgumentParser(description="Validate OFD against GB/T 33190-2016 Appendix A schemas")
    ap.add_argument("target", nargs="?", help=".ofd file or extracted directory")
    ap.add_argument("--selfcheck", action="store_true", help="validate bundled schemas themselves")
    args = ap.parse_args()

    if args.selfcheck:
        sys.exit(1 if selfcheck() else 0)

    if not args.target:
        ap.print_help()
        sys.exit(2)

    paths, base = iter_xml_paths(args.target)
    if not paths:
        print("No .xml found in %s (pass a .ofd file or an extracted directory)" % args.target)
        sys.exit(2)

    total = passed = failed = skipped = 0
    for p in paths:
        res, msg = validate_xml_file(p)
        total += 1
        if res is True:
            passed += 1
            status = "PASS"
        elif res is False:
            failed += 1
            status = "FAIL"
        else:
            skipped += 1
            status = "SKIP"
        rel = os.path.relpath(p, base) if base else p
        print("[%s] %s -> %s" % (status, rel, msg))

    print("\n%d files: %d PASS, %d FAIL, %d SKIP" % (total, passed, failed, skipped))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
