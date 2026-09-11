#!/usr/bin/env python3
"""ofdreader command-line interface.

Examples
--------
    # extract text + embedded images, write a structured Markdown report
    python cli.py "北京点聚红头文件.ofd" --md out.md --images --out images

    # just print text to stdout
    python cli.py document.ofd --text

    # structural + (if available) Appendix-A schema validation
    python cli.py document.ofd --validate

    # show metadata, outline, signatures, annotations and actions
    python cli.py document.ofd --info
"""

from __future__ import annotations

import os
import re
import sys
import argparse

# Make the script runnable from any cwd: the ofdreader package sits next to it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ofdreader import open_ofd
from ofdreader import extract as ex
from ofdreader import validate as vd


# ---------------------------------------------------------------------------
# formatting helpers
# ---------------------------------------------------------------------------


_SIG_DT = re.compile(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})")


def _fmt_sig_datetime(s):
    """``20250821064935Z`` -> ``2025-08-21 06:49:35Z`` (leave odd values as-is)."""
    if not s:
        return None
    m = _SIG_DT.match(s.strip())
    if m:
        y, mo, d, h, mi, sec = m.groups()
        return "%s-%s-%s %s:%s:%sZ" % (y, mo, d, h, mi, sec)
    return s


def _fmt_action(a):
    if a.kind == "Goto":
        if a.dest:
            return "Goto -> page %s (type=%s)" % (a.dest.get("page_id"), a.dest.get("type"))
        return "Goto -> bookmark %s" % a.bookmark
    if a.kind == "URI":
        return "URI -> %s" % a.uri
    if a.kind:
        return "%s -> %s" % (a.kind, a.attrs or "")
    return "unknown"


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------


def _print_info(doc, cont):
    di = doc.doc_info
    print("OFD  %s (v%s, %s)" % (di.title or "<untitled>", doc.version, doc.doc_type))
    print("  Author : %s" % di.author)
    print("  Creator: %s" % di.creator)
    print("  DocID  : %s" % di.doc_id)
    print("  Created: %s   Modified: %s" % (di.creation_date, di.mod_date))
    if di.custom:
        print("  Custom : %s" % di.custom)
    print("  Pages  : %d   PageArea: %s" % (len(doc.pages), doc.page_area))

    if doc.outlines:
        print("  Outline:")
        for o in doc.outlines:
            print("    - %s  (page %s)" % (o.title, o.page_id))

    _print_signatures(doc)
    _print_annotations(doc)
    _print_actions(doc, cont)


def _print_signatures(doc):
    if not doc.signatures:
        print("  Signatures: none")
        return
    print("  Signatures: %d" % len(doc.signatures))
    for s in doc.signatures:
        print("    - #%s type=%s provider=%s(%s) company=%s" % (
            s.sign_id, s.type, s.provider_name, s.provider_version, s.provider_company))
        print("      signed at : %s" % _fmt_sig_datetime(s.signature_datetime))
        print("      method    : %s   digest: %s" % (s.signature_method, s.check_method))
        print("      protected : %d file(s)" % len(s.references))
        if s.stamp_annot:
            print("      stamp     : page %s  boundary %s" % (
                s.stamp_annot.get("page_ref"), s.stamp_annot.get("boundary")))
        if s.signed_value_path:
            ok = os.path.isfile(s.signed_value_path)
            print("      sign value: %s (%s)" % (os.path.basename(s.signed_value_path),
                                                 "present" if ok else "MISSING"))


def _print_annotations(doc):
    if not doc.annotations:
        print("  Annotations: none")
        return
    print("  Annotations: %d" % len(doc.annotations))
    for a in doc.annotations:
        print("    - page %s  #%s  type=%s  by %s  %s" % (
            a.page_id, a.annot_id, a.type, a.creator, a.boundary or ""))
        if a.remark:
            print("      remark: %s" % a.remark)
        for act in a.actions:
            print("      action: %s" % _fmt_action(act))


def _print_actions(doc, cont):
    parser = getattr(doc, "parser", None)
    total = list(doc.actions)
    per_page = []
    if parser is not None:
        for p in doc.pages:
            roots = parser.load_page_content_expanded(p)
            acts = ex.extract_actions(*roots)
            if acts:
                per_page.append((p.index, acts))
                total.extend(acts)
    if not total:
        print("  Actions: none")
        return
    print("  Actions: %d" % len(total))
    for a in doc.actions:
        print("    - [doc] event=%s  %s" % (a.event, _fmt_action(a)))
    for idx, acts in per_page:
        for a in acts:
            print("    - [page %d] event=%s owner=%s  %s" % (
                idx, a.event, a.context, _fmt_action(a)))


# ---------------------------------------------------------------------------
# page iteration / extraction
# ---------------------------------------------------------------------------


def _iter_pages(cont, doc):
    """Yield (page, content_roots).

    ``content_roots`` is the ordered list of layers for the page — background
    templates, the page's own content, then foreground templates (§7.7) — so
    header/footer/red-header content on a template is never dropped.
    """
    parser = getattr(doc, "parser", None)
    for p in doc.pages:
        try:
            if parser is not None:
                roots = parser.load_page_content_expanded(p)
            else:
                roots = [cont.read_xml(p.content_loc, base_dir=p.content_base_dir)]
        except Exception:  # noqa: BLE001
            roots = []
        yield p, roots


def _composite_reg(doc):
    return getattr(doc, "registry", None)


def _do_text(doc, cont):
    for p, roots in _iter_pages(cont, doc):
        lines = ex.extract_page_text(*roots, composite_reg=_composite_reg(doc))
        print("\n===== 第 %d 页 =====" % p.index)
        for ln in lines:
            print(ln)


def _do_md(path, doc, cont):
    di = doc.doc_info
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# %s\n\n" % (di.title or "OFD 文档"))
        f.write("- **版本**: %s  **类型**: %s\n" % (doc.version, doc.doc_type))
        f.write("- **作者**: %s  **创建工具**: %s\n" % (di.author, di.creator))
        f.write("- **DocID**: %s\n" % di.doc_id)
        f.write("- **创建/修改**: %s / %s\n" % (di.creation_date, di.mod_date))
        f.write("- **页数**: %d\n\n" % len(doc.pages))

        if doc.outlines:
            f.write("## 大纲\n\n")
            for o in doc.outlines:
                f.write("- %s\n" % o.title)
            f.write("\n")

        _md_signatures(f, doc)
        _md_annotations(f, doc)

        for p, roots in _iter_pages(cont, doc):
            lines = ex.extract_page_text(*roots, composite_reg=_composite_reg(doc))
            f.write("## 第 %d 页\n\n" % p.index)
            if lines:
                f.write("\n".join(lines) + "\n\n")
            else:
                f.write("_(无文本图层)_\n\n")
    print("wrote Markdown -> %s" % path)


def _md_signatures(f, doc):
    if not doc.signatures:
        return
    f.write("## 数字签名\n\n")
    for s in doc.signatures:
        f.write("- **签名 #%s**（%s）\n" % (s.sign_id, s.type))
        f.write("  - 提供者: %s %s (%s)\n" % (s.provider_name, s.provider_version, s.provider_company))
        f.write("  - 签名时间: %s\n" % _fmt_sig_datetime(s.signature_datetime))
        f.write("  - 算法: %s / 摘要 %s\n" % (s.signature_method, s.check_method))
        f.write("  - 保护文件数: %d\n" % len(s.references))
        if s.stamp_annot:
            f.write("  - 签章位置: 页 %s  %s\n" % (
                s.stamp_annot.get("page_ref"), s.stamp_annot.get("boundary")))
        if s.signed_value_path:
            f.write("  - 签名值: %s\n" % os.path.basename(s.signed_value_path))
    f.write("\n")


def _md_annotations(f, doc):
    if not doc.annotations:
        return
    f.write("## 注释\n\n")
    for a in doc.annotations:
        f.write("- **页 %s / #%s**（%s，%s）\n" % (a.page_id, a.annot_id, a.type, a.creator))
        if a.remark:
            f.write("  - %s\n" % a.remark)
        for act in a.actions:
            f.write("  - 动作: %s\n" % _fmt_action(act))
    f.write("\n")


def _do_images(doc, cont, out_dir):
    total = 0
    for p, roots in _iter_pages(cont, doc):
        if not roots:
            continue
        saved = ex.extract_page_images(
            *roots, registry=doc.registry, cont=cont, out_dir=out_dir,
            page_index=p.index, composite_reg=_composite_reg(doc),
        )
        total += len(saved)
        for s in saved:
            print("  saved %s" % s)
    print("extracted %d image(s) -> %s" % (total, out_dir))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ofdreader", description="Extract text/images/metadata from OFD (GB/T 33190-2016) files.")
    ap.add_argument("ofd", help="path to .ofd file or extracted directory")
    ap.add_argument("--text", action="store_true", help="print extracted text to stdout")
    ap.add_argument("--md", metavar="OUT.md", help="write structured Markdown extraction")
    ap.add_argument("--images", action="store_true", help="extract embedded images")
    ap.add_argument("--out", default="ofd_output", help="output dir for images (default: ofd_output)")
    ap.add_argument("--info", action="store_true", help="print document metadata / outline / signatures / annotations")
    ap.add_argument("--validate", action="store_true", help="run structural (and schema, if available) validation")
    args = ap.parse_args(argv)

    if not any([args.text, args.md, args.images, args.info, args.validate]):
        args.info = True
        args.text = True

    try:
        cont, doc = open_ofd(args.ofd)
    except Exception as e:  # noqa: BLE001
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    try:
        if args.info:
            _print_info(doc, cont)
        if args.validate:
            print("\n--- structural validation ---")
            for level, msg in vd.lenient_check(cont, doc):
                print("[%s] %s" % (level, msg))
            avail, out = vd.schema_check(args.ofd)
            if avail:
                print("\n--- Appendix-A schema check (ofd-standard skill) ---")
                print(out)
            else:
                print("\n(schema check skipped: %s)" % out)
        if args.text:
            _do_text(doc, cont)
        if args.md:
            _do_md(args.md, doc, cont)
        if args.images:
            print("\n--- image extraction ---")
            _do_images(doc, cont, args.out)
    finally:
        cont.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
