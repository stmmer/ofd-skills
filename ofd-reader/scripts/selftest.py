#!/usr/bin/env python3
"""Build a synthetic OFD exercising the features the sample file lacks.

The real-world sample (WPS/点聚 红头文件) has no template pages, no annotations,
no composite objects and no page-level actions, so those code paths would
otherwise ship untested. This script synthesises a minimal but schema-shaped
OFD containing all of them, then asserts that ofdreader picks each one up.

Run:  python tests/build_and_test.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

# Locate the ofdreader package: works from the repo (tests/ -> repo root) and
# from the packaged skill (scripts/ -> scripts/ofdreader).
_HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.dirname(_HERE), _HERE):
    if os.path.isdir(os.path.join(_cand, "ofdreader")):
        sys.path.insert(0, _cand)
        break

from ofdreader import open_ofd                      # noqa: E402
from ofdreader import extract as ex                 # noqa: E402

NS = 'xmlns:ofd="http://www.ofdspec.org/2016"'

OFD_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:OFD {NS} DocType="OFD" Version="1.1">
  <ofd:DocBody>
    <ofd:DocInfo>
      <ofd:Title>synthetic fixture</ofd:Title>
      <ofd:Author>ofdreader tests</ofd:Author>
    </ofd:DocInfo>
    <ofd:DocRoot>Doc_0/Document.xml</ofd:DocRoot>
    <ofd:Signatures>/Doc_0/Signs/Signatures.xml</ofd:Signatures>
  </ofd:DocBody>
</ofd:OFD>
'''

# CommonData declares a template page (§7.7) holding the red header + header.
DOCUMENT_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Document {NS}>
  <ofd:CommonData>
    <ofd:MaxUnitID>999</ofd:MaxUnitID>
    <ofd:PageArea><ofd:PhysicalBox>0 0 210 297</ofd:PhysicalBox></ofd:PageArea>
    <ofd:PublicRes>PublicRes.xml</ofd:PublicRes>
    <ofd:DocumentRes>DocumentRes.xml</ofd:DocumentRes>
    <ofd:TemplatePage ID="900" Name="RedHeader" ZOrder="Background"
                      BaseLoc="Templates/Tpl_0/Content.xml"/>
  </ofd:CommonData>
  <ofd:Pages>
    <ofd:Page ID="1" BaseLoc="Pages/Page_0/Content.xml"/>
  </ofd:Pages>
  <ofd:Annotations>Annotations.xml</ofd:Annotations>
</ofd:Document>
'''

# The template page: red header + running header, drawn *under* the page.
TEMPLATE_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Page {NS}>
  <ofd:Content>
    <ofd:Layer ID="9001">
      <ofd:TextObject ID="901" Boundary="20 10 120 12" Font="1" Size="8">
        <ofd:TextCode X="0" Y="10">红头：某某单位文件</ofd:TextCode>
      </ofd:TextObject>
      <ofd:TextObject ID="902" Boundary="20 25 60 6" Font="1" Size="4">
        <ofd:TextCode X="0" Y="5">页眉内容</ofd:TextCode>
      </ofd:TextObject>
    </ofd:Layer>
  </ofd:Content>
</ofd:Page>
'''

# Page content: body text, a text run carrying a URI action (§14), and a
# CompositeObject (§13) whose real text lives in the resource, not here.
PAGE_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Page {NS}>
  <ofd:Template TemplateID="900" ZOrder="Background"/>
  <ofd:Content>
    <ofd:Layer ID="2">
      <ofd:TextObject ID="10" Boundary="20 100 60 10" Font="1" Size="5">
        <ofd:TextCode X="0" Y="8">正文第一页</ofd:TextCode>
      </ofd:TextObject>
      <ofd:TextObject ID="11" Boundary="20 120 60 10" Font="1" Size="5">
        <ofd:Actions>
          <ofd:Action Event="CLICK">
            <ofd:URI URI="https://example.com/doc" Base="https://example.com"/>
          </ofd:Action>
        </ofd:Actions>
        <ofd:TextCode X="0" Y="8">点击访问</ofd:TextCode>
      </ofd:TextObject>
      <ofd:CompositeObject ID="12" Boundary="20 140 100 20" ResourceID="77"/>
    </ofd:Layer>
  </ofd:Content>
</ofd:Page>
'''

PUBLIC_RES_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Res {NS} BaseLoc="Res">
  <ofd:Fonts>
    <ofd:Font ID="1" FontName="SimSun" FamilyName="宋体"/>
  </ofd:Fonts>
</ofd:Res>
'''

# The composite graphic unit (§13): its <Content> holds the actual text.
DOCUMENT_RES_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Res {NS} BaseLoc="Res">
  <ofd:CompositeGraphicUnits>
    <ofd:CompositeGraphicUnit ID="77" Width="100" Height="20">
      <ofd:Content>
        <ofd:TextObject ID="80" Boundary="20 140 80 10" Font="1" Size="5">
          <ofd:TextCode X="0" Y="8">复合对象内文字</ofd:TextCode>
        </ofd:TextObject>
      </ofd:Content>
    </ofd:CompositeGraphicUnit>
  </ofd:CompositeGraphicUnits>
</ofd:Res>
'''

ANNOTATIONS_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Annotations {NS}>
  <ofd:Page PageID="1"><ofd:FileLoc>Annots/Page_1.xml</ofd:FileLoc></ofd:Page>
</ofd:Annotations>
'''

PAGE_ANNOT_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:PageAnnot {NS}>
  <ofd:Annot ID="500" Type="Link" Creator="tester" LastModDate="2026-09-10" Visible="true">
    <ofd:Remark>这是一个链接注释</ofd:Remark>
    <ofd:Appearance Boundary="20 200 60 10"/>
  </ofd:Annot>
  <ofd:Annot ID="501" Type="Stamp" Creator="tester" LastModDate="2026-09-10">
    <ofd:Actions>
      <ofd:Action Event="CLICK">
        <ofd:Goto><ofd:Dest Type="XYZ" PageID="1" Left="10" Top="20"/></ofd:Goto>
      </ofd:Action>
    </ofd:Actions>
    <ofd:Appearance Boundary="30 210 40 40"/>
  </ofd:Annot>
</ofd:PageAnnot>
'''

SIGNATURES_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Signatures {NS}>
  <ofd:MaxSignId>1</ofd:MaxSignId>
  <ofd:Signature ID="1" BaseLoc="Sign_1/Signature.xml" Type="Seal"/>
</ofd:Signatures>
'''

SIGNATURE_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<ofd:Signature {NS}>
  <ofd:SignedInfo>
    <ofd:Provider ProviderName="TEST" Version="1.0" Company="Fixture"/>
    <ofd:SignatureDateTime>20260101120000Z</ofd:SignatureDateTime>
    <ofd:SignatureMethod>1.2.156.10197.1.501</ofd:SignatureMethod>
    <ofd:References CheckMethod="1.2.156.10197.1.401">
      <ofd:Reference FileRef="../../Document.xml">
        <ofd:CheckValue>AAAA</ofd:CheckValue>
      </ofd:Reference>
    </ofd:References>
    <ofd:StampAnnot ID="2" PageRef="1" Boundary="42.21 98.80 42.04 42.03"/>
  </ofd:SignedInfo>
  <ofd:SignedValue>SignValue.dat</ofd:SignedValue>
</ofd:Signature>
'''

FILES = {
    "OFD.xml": OFD_XML,
    "Doc_0/Document.xml": DOCUMENT_XML,
    "Doc_0/Templates/Tpl_0/Content.xml": TEMPLATE_XML,
    "Doc_0/Pages/Page_0/Content.xml": PAGE_XML,
    "Doc_0/PublicRes.xml": PUBLIC_RES_XML,
    "Doc_0/DocumentRes.xml": DOCUMENT_RES_XML,
    "Doc_0/Annotations.xml": ANNOTATIONS_XML,
    "Doc_0/Annots/Page_1.xml": PAGE_ANNOT_XML,
    "Doc_0/Signs/Signatures.xml": SIGNATURES_XML,
    "Doc_0/Signs/Sign_1/Signature.xml": SIGNATURE_XML,
    "Doc_0/Signs/Sign_1/SignValue.dat": "binary-signature-bytes",
}


def build(root: str):
    for rel, data in FILES.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "w" if isinstance(data, str) else "wb"
        with open(path, mode, encoding="utf-8" if mode == "w" else None) as f:
            f.write(data)


def main():
    tmp = tempfile.mkdtemp(prefix="ofd_fixture_")
    failures = []

    def check(label, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print("[%s] %s%s" % (status, label, ("  -- " + detail) if detail and not cond else ""))
        if not cond:
            failures.append(label)

    try:
        build(tmp)
        cont, doc = open_ofd(tmp)
        page = doc.pages[0]
        roots = doc.parser.load_page_content_expanded(page)
        reg = doc.registry

        # 1. template page expansion
        check("template page is expanded into the page layers",
              len(roots) == 2, "roots=%d" % len(roots))

        lines = ex.extract_page_text(*roots, composite_reg=reg)
        text = "\n".join(lines)
        check("template text (red header) is captured",
              "红头：某某单位文件" in text, text)
        check("template text (header) is captured", "页眉内容" in text, text)
        check("page body text is captured", "正文第一页" in text, text)
        check("template content is ordered above body content",
              "红头" in text and text.index("红头") < text.index("正文第一页"), text)

        # 2. composite objects
        check("composite object text is expanded from the resource",
              "复合对象内文字" in text, text)
        comps = list(ex.iter_composite_objects(*roots))
        check("composite object element is discoverable", len(comps) == 1, str(len(comps)))

        # 3. actions
        acts = ex.extract_actions(*roots)
        check("page-level action is extracted", len(acts) == 1, str(len(acts)))
        if acts:
            a = acts[0]
            check("action is a URI action", a.kind == "URI" and a.uri == "https://example.com/doc",
                  "%s %s" % (a.kind, a.uri))
            check("action records its owner object", a.context == "TextObject", str(a.context))
            check("action records its event", a.event == "CLICK", str(a.event))

        # 4. annotations
        check("annotations are parsed", len(doc.annotations) == 2, str(len(doc.annotations)))
        by_id = {a.annot_id: a for a in doc.annotations}
        check("link annotation type/remark parsed",
              by_id.get("500") and by_id["500"].type == "Link"
              and by_id["500"].remark == "这是一个链接注释",
              str(by_id.get("500")))
        check("annotation is bound to its page",
              by_id.get("500") and by_id["500"].page_id == "1",
              str(by_id.get("500") and by_id["500"].page_id))
        stamp = by_id.get("501")
        check("annotation with an embedded action is parsed",
              stamp and len(stamp.actions) == 1 and stamp.actions[0].kind == "Goto",
              str(stamp.actions if stamp else None))
        check("annotation appearance boundary parsed",
              stamp and stamp.boundary == (30.0, 210.0, 40.0, 40.0), str(stamp.boundary if stamp else None))

        # 5. signatures
        check("signature is parsed", len(doc.signatures) == 1, str(len(doc.signatures)))
        if doc.signatures:
            s = doc.signatures[0]
            check("signature provider parsed",
                  s.provider_name == "TEST" and s.provider_company == "Fixture", str(s.provider_name))
            check("signature digest refs parsed", len(s.references) == 1, str(len(s.references)))
            check("signature stamp annot parsed",
                  s.stamp_annot and s.stamp_annot["page_ref"] == "1", str(s.stamp_annot))
            check("signed value file resolves",
                  s.signed_value_path and os.path.isfile(s.signed_value_path), str(s.signed_value_path))

        cont.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n%d failure(s)" % len(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
