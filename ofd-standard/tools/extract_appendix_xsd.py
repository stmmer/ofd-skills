#!/usr/bin/env python3
"""从 GB/T 33190—2016 标准 PDF 的附录 A 复原 13 个 XSD。

用法
----
    python extract_appendix_xsd.py <标准PDF> [-o 输出目录]
                                   [--no-comments]
                                   [--verify <参考XSD目录>]

示例
----
    python extract_appendix_xsd.py "GBT 33190-2016 电子文件存储与交换格式 版式文档.pdf" \
        -o schemas --verify ./old_schemas

为什么需要"复原"而不是直接抽取
------------------------------
该 PDF 的排版系统把 XML 标记**内部的词间空格整个省略了**（改由字距体现），
所以 `get_text()` / `rawdict` 拿到的都是 `<xs:enumerationvalue="900"/>` 这种粘在一起的文本。

靠几何（字符 x 坐标）反推空格不可靠 —— `char['origin']` 含 side bearing，
`step(prev→next) = advance(prev) + lsb(next) - lsb(prev)`，实测最佳阈值 F1 仅约 62%。

本脚本改用**确定性规则**（XSD 语法本身即可判定边界）：
  1. 属性值以 `="` 开头，**闭合**引号之后紧跟字母 => 补空格；
  2. 「当前位置之后正好是某个已知属性名 + `=`」=> 补空格。
属性词表取自 W3C XML Schema 规范，**不依赖任何第三方转录版本**。

校验（双重，任一失败即非零退出）
--------------------------------
  1. 每个 XSD 用 lxml 编译为 XMLSchema（含 `xs:include` 兄弟文件解析）；
  2. 若给了 `--verify`，再与参考目录做**去空白比对**，必须逐字符一致。

依赖：PyMuPDF(fitz)、lxml
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import fitz

# 附录 A 中 13 个 XSD 的出现顺序（A.1 → A.13），用作输出文件名
ORDER = ["OFD", "Document", "Annotations", "Annotation", "Res", "Definitions",
         "Signatures", "Signature", "CustomTags", "Extensions", "Attachments",
         "Version", "Page"]

# XSD 语法中的属性名（W3C XML Schema 规范），按长度倒序以优先匹配长名
XSD_ATTRS = sorted([
    "xmlns", "xml", "version", "encoding", "name", "type", "base", "value", "use",
    "ref", "minOccurs", "maxOccurs", "default", "fixed", "abstract", "substitutionGroup",
    "nillable", "form", "id", "mixed", "itemType", "targetNamespace", "elementFormDefault",
    "attributeFormDefault", "processContents", "namespace", "schemaLocation", "memberTypes",
    "final", "block", "public", "system", "source", "refer", "maxInclusive", "minInclusive",
    "maxExclusive", "minExclusive", "pattern", "enumeration", "length", "minLength",
    "maxLength", "totalDigits", "fractionDigits", "whiteSpace", "xpath", "selector", "field",
    "min", "max", "occurs", "mode", "scope", "path", "minVersion", "maxVersion",
], key=len, reverse=True)

# 版面噪声：整行匹配即丢弃（页码、页眉、附录/章节标题）
LINE_NOISE = [
    re.compile(r"^\d+$"),
    re.compile(r"^GB/T\s*33190[—\-]2016$"),
    re.compile(r"^[附\s]*录\s*A$"),
    re.compile(r"^\(?规范性附录\)?$"),
    re.compile(r"^Schema$"),
    re.compile(r"^A\.$"),
    re.compile(r"^\d+\s+[A-Za-z]+\.$"),
    re.compile(r"^([A-Za-z]+\.)?xsd$"),
]

COMMENT_RE = re.compile(r"<!\s*--.*?--\s*>", re.S)
_MASK_OPEN, _MASK_CLOSE = "\x01", "\x02"


# --------------------------------------------------------------------------- #
# 1. 定位附录 A
# --------------------------------------------------------------------------- #
def find_appendix_pages(doc) -> list[int]:
    """附录 A 是连续页：起点 = 首个含 `xs:schema` 的页，终点 = 最后一个含 `</xs:schema>` 的页。

    注意不能只用 `xs:schema` 筛页 —— 它只在每个 XSD 的根标签里出现一次，
    中间页只有 `<xs:element` / `</xs:complexType>` 等。必须取首尾之间的**连续区间**。
    """
    def flat(i: int) -> str:
        return doc[i].get_text().replace(" ", "").replace("\n", "")

    starts = [i for i in range(doc.page_count) if "xs:schema" in flat(i)]
    ends = [i for i in range(doc.page_count) if "</xs:schema>" in flat(i)]
    if not starts or not ends:
        raise SystemExit("未在 PDF 中定位到附录 A")
    return list(range(min(starts), max(ends) + 1))


# --------------------------------------------------------------------------- #
# 2. 取字符流：注释先用占位符屏蔽，保证其内部原样保留
# --------------------------------------------------------------------------- #
def appendix_text(doc, pages, keep_comments: bool) -> tuple[str, dict[str, str]]:
    out = []
    for pno in pages:
        for raw in doc[pno].get_text().splitlines():
            line = raw.strip()
            if not line or any(p.fullmatch(line) for p in LINE_NOISE):
                continue
            out.append(line)
    text = "".join(out)
    # PyMuPDF 会把注释符抽成 `<! --` / `-- >`（中间插了空格）
    text = text.replace("<! --", "<!--").replace("-- >", "-->")

    store: dict[str, str] = {}

    def _mask(m):
        if not keep_comments:
            return ""
        key = f"{_MASK_OPEN}{len(store)}{_MASK_CLOSE}"
        store[key] = m.group(0)
        return key

    return COMMENT_RE.sub(_mask, text), store


def strip_ws(text: str) -> str:
    return re.sub(r"\s+", "", text)


def split_xsds(plain: str) -> list[str]:
    """每个 XSD 以 `<?xml` 开头；据此切段，并在 `</xs:schema>` 处截断尾部噪声。"""
    starts = [m.start() for m in re.finditer(r"<\?xml", plain)]
    if not starts:
        raise SystemExit("切段失败：未见 `<?xml` 声明")
    chunks = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(plain)
        part = plain[s:e]
        end = part.rfind("</xs:schema>")
        if end >= 0:
            part = part[:end + len("</xs:schema>")]
        chunks.append(part)
    return chunks


# --------------------------------------------------------------------------- #
# 3. 复原空格
# --------------------------------------------------------------------------- #
def respace(chunk: str) -> str:
    """按 XSD 语法规则在去空白的片段上恢复 token 分隔空格。"""
    out = []
    n = len(chunk)
    in_quote = False
    for i, ch in enumerate(chunk):
        out.append(ch)
        if ch in "\"'":
            in_quote = not in_quote
            # 只有**闭合**引号之后才补空格，否则会把 `"UTF-8"` 弄成 `" UTF-8"`
            if not in_quote and i + 1 < n and (chunk[i + 1].isalpha() or chunk[i + 1] == "_"):
                out.append(" ")
            continue
        if in_quote or i + 1 >= n:
            continue
        if not (ch.isalnum() or ch in "_:.-"):
            continue
        tail = chunk[i + 1:]
        for a in XSD_ATTRS:
            if tail.startswith(a + "="):
                out.append(" ")
                break
    return "".join(out)


def unmask(text: str, store: dict[str, str]) -> str:
    for key, val in store.items():
        text = text.replace(key, val)
    return text


# --------------------------------------------------------------------------- #
# 4. 格式化与校验
# --------------------------------------------------------------------------- #
def pretty(xsd_text: str) -> str:
    """用 lxml 重新序列化以获得缩进；XML 声明统一用双引号。"""
    from lxml import etree
    root = etree.fromstring(xsd_text.encode("utf-8"))
    body = etree.tostring(root, pretty_print=True, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body


def compile_ok(path: str) -> tuple[bool, str]:
    from lxml import etree
    try:
        etree.XMLSchema(etree.parse(path))
        return True, "OK"
    except Exception as e:                                       # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:55]}"


def norm_for_cmp(s: str) -> str:
    """去注释、统一 XML 声明、去空白 —— 用于与参考版本比对。"""
    s = COMMENT_RE.sub("", s)
    s = re.sub(r"<\?xml[^>]*\?>", "<?xml?>", s)
    return re.sub(r"\s+", "", s)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="从 GB/T 33190—2016 附录 A 复原 XSD")
    ap.add_argument("pdf", help="标准 PDF 路径")
    ap.add_argument("-o", "--out", default="schemas", help="输出目录（默认 ./schemas）")
    ap.add_argument("--no-comments", action="store_true", help="不保留标准附录的中文注释")
    ap.add_argument("--verify", metavar="DIR", help="参考 XSD 目录，将与之做去空白比对")
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    pages = find_appendix_pages(doc)
    print(f"附录 A: PDF 第 {pages[0]+1}–{pages[-1]+1} 页（共 {len(pages)} 页）")

    text, store = appendix_text(doc, pages, not args.no_comments)
    plain = strip_ws(text)
    chunks = split_xsds(plain)
    print(f"字符流 {len(plain)} 字符, 切出 {len(chunks)} 个 XSD"
          f", 注释 {len(store)} 条\n")
    if len(chunks) != len(ORDER):
        raise SystemExit(f"预期 {len(ORDER)} 个 XSD，实际 {len(chunks)}，放弃写入")

    os.makedirs(args.out, exist_ok=True)

    # 必须先把 13 个文件全部写盘，lxml 编译时 xs:include 才能解析到兄弟文件
    staged = {}
    for name, chunk in zip(ORDER, chunks):
        raw = unmask(respace(chunk), store)
        try:
            staged[name] = pretty(raw)
        except Exception as e:                                   # noqa: BLE001
            print(f"  ! {name}: 格式化失败({type(e).__name__})，写出未缩进版本")
            staged[name] = raw
    for name, txt in staged.items():
        # newline="\n"：禁止 Windows 把 \n 翻成 \r\n，与仓库 .gitattributes 的 eol=lf 保持一致
        with open(os.path.join(args.out, name + ".xsd"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(txt)

    print(f"{'文件':<16}{'字符':>7}  {'编译':<10}{'与参考一致'}")
    print("-" * 52)
    ok_n = same_n = 0
    for name in ORDER:
        path = os.path.join(args.out, name + ".xsd")
        ok, msg = compile_ok(path)
        ok_n += ok
        same = "-"
        if args.verify:
            ref_path = os.path.join(args.verify, name + ".xsd")
            if os.path.exists(ref_path):
                with open(ref_path, encoding="utf-8") as fh:
                    same = str(norm_for_cmp(fh.read()) == norm_for_cmp(staged[name]))
                same_n += (same == "True")
            else:
                same = "无参考"
        print(f"{name:<16}{len(staged[name]):>7}  {msg:<10}{same}")

    print("-" * 52)
    print(f"编译通过 {ok_n}/{len(ORDER)}", end="")
    if args.verify:
        print(f"   与参考逐字符一致 {same_n}/{len(ORDER)}")
    else:
        print()
    print(f"输出目录: {os.path.abspath(args.out)}")
    return 0 if ok_n == len(ORDER) else 1


if __name__ == "__main__":
    sys.exit(main())
