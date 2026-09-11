---
name: ofd-reader
description: "Dependency-free OFD (GB/T 33190-2016 版式文档) parser and extractor. Use when a task involves reading, parsing, validating, or extracting content from .ofd files — text, embedded images, metadata, outlines, annotations, digital signatures, template pages, composite objects, or actions — or converting OFD to Markdown/text. Pure Python stdlib, no pip install required."
---

<!-- argument-hint: [path to .ofd, and what to extract: text | images | md | info | validate] -->

# OFD Reader — 解析 GB/T 33190—2016 版式文档

一个**纯标准库**的 OFD 解析器（zipfile + xml.etree.ElementTree，零外部依赖）。
打开 ZIP 容器 → 沿 `OFD.xml → DocBody → DocRoot` 主链 → 展开模板页 → 抽取文本 / 图像 /
注释 / 动作 / 数字签名。已在真实产商文件（WPS / 点聚，OFD **v1.1**）上端到端验证。

> 配套 skill：`ofd-standard`（GB/T 33190—2016 知识库 + 13 个附录 A XSD）。
> 那个是**契约基准与严格校验**，这个是**实际解析执行器**。
> 需要核对某个元素的规范定义时去查 `ofd-standard`；需要真的把文件读出来时用本 skill。

## When to Use

- 用户给了 `.ofd` 文件，要读内容、提文本、导图、转 Markdown
- 需要检查 OFD 结构是否完好、页/资源/签名是否可解析
- 需要抽取数字签名信息、注释、链接动作、模板页（红头/页眉）

## Quick Start

```bash
PY="python"   # 或托管 Python 绝对路径
SK="~/.workbuddy/skills/ofd-reader/scripts"

# 最常用：文本 + 图像 + 结构化 Markdown
"$PY" "$SK/cli.py" "文档.ofd" --md out.md --images --out images

# 只看元信息 / 大纲 / 签名 / 注释 / 动作
"$PY" "$SK/cli.py" "文档.ofd" --info

# 只看文本
"$PY" "$SK/cli.py" "文档.ofd" --text

# 结构校验（宽松）；装了 lxml 且 ofd-standard 在场时追加附录 A 强校验
"$PY" "$SK/cli.py" "文档.ofd" --validate
```

不带任何参数时等价于 `--info --text`。

**Windows 路径**：必须传带盘符的绝对路径（`C:/...` 或 `C:\...`），
不要写 `/c/...` / `/f/...`（会被当成盘相对路径，输出落到错误位置）。

## Python API

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.workbuddy/skills/ofd-reader/scripts"))

from ofdreader import open_ofd
from ofdreader import extract as ex

cont, doc = open_ofd("文档.ofd")

print(doc.doc_info.title, doc.version, len(doc.pages))

for page in doc.pages:
    # 展开模板层（红头/页眉/水印）+ 本页内容，按绘制顺序返回
    roots = doc.parser.load_page_content_expanded(page)
    lines = ex.extract_page_text(*roots, composite_reg=doc.registry)   # 阅读顺序
    imgs  = ex.extract_page_images(*roots, registry=doc.registry, cont=cont,
                                   out_dir="out", page_index=page.index,
                                   composite_reg=doc.registry)
    acts  = ex.extract_actions(*roots)      # 页内链接/URI 动作
cont.close()
```

`doc` 上直接可用的结果：

| 字段 | 内容 | 章节 |
|---|---|---|
| `doc.signatures` | `SignatureInfo`：提供者、签名时间、算法、被保护文件摘要、签章位置、签名值路径 | §18 |
| `doc.annotations` | `AnnotationInfo`：所属页、类型、作者、外观边界、备注、携带动作 | §15 |
| `doc.actions` | 文档级动作 | §14 |
| `doc.outlines` | 大纲（含跳转目标页） | §7.8 |
| `doc.pages` | 页信息；配合 `doc.parser.load_page_content_expanded()` 展开模板层 | §7.7 |
| `doc.registry` | 资源表（`resolve_media` / `resolve_font` / `resolve_composite`） | §7.9 |

## What It Handles

| 能力 | 做法 |
|---|---|
| **模板页展开** | `<Template TemplateID ZOrder/>` → 按 Background/前景分层展开，嵌套递归 + 环检测。**不展开会整层丢掉红头/页眉** |
| **复合对象** | `CompositeObject@ResourceID` → 资源里 `CompositeGraphicUnit/Content` 展开内部图元；自引用阻断 |
| **注释** | 两级：`Document/Annotations` → 入口文件（按 PageID 索引）→ 每页 `PageAnnot` |
| **动作** | Goto(Dest\|Bookmark) / URI / GotoA / Sound / Movie，保留 Event 与宿主对象 |
| **数字签名** | `DocBody/Signatures` → `Signatures.xml` → `Sign_N/Signature.xml` + `SignValue.dat` |
| **文本阅读顺序** | 逐字形坐标 → 按 Y 聚类成行 → 行内按 X 排序 → 间距阈值插空格 |
| **图像** | 三级资源作用域（页→文档→公共）解析 MediaFile 并落盘 |

## Parsing Strategy — 为什么能吃掉真实文件

1. **命名空间无关**：按 local-name 匹配，不依赖 `ofd:` 前缀。
2. **宽松校验**：OFD v1.1、数字型 `ST_ID`、厂商扩展节点一律不拒绝，只报真问题。
3. **属性优先**：真实文件里 `Page/@BaseLoc`、`Page/@ID`、`OutlineElem/@Title`、
   `TemplatePage/@BaseLoc` 都是**属性**而非子元素。
   注意：标准正文用「名称/类型/说明/备注」**平铺表格**描述结构（如 §7.6 表11 把
   `Page`、`ID`、`BaseLoc` 并排列为三行），元素与其属性同表分行，**极易被误读成父子关系**
   —— 这是标准的表格体例，不是 OCR 损坏。判断以附录 A 的 XSD 为准。
4. **模板层优先展开**：避免漏抽红头/页眉/水印。

更多踩坑细节见 `references/pitfalls.md`。

## Limitations

- **不渲染**：只抽取，不绘制版式（无 CTM 到像素换算、无 PathObject 矢量重绘）。
- **不验签**：只抽签名描述与摘要清单，不做 SM2/SM3 密码学验签。
- **字型**：只解析字体引用，不嵌入字形轮廓（文本为 Unicode 字符串）。

## Self-test

技能自带合成样例自检（覆盖模板页 / 复合对象 / 注释 / 动作 / 签名 —— 这些在多数真实
样例文件里都不存在，不造 fixture 就等于没测）：

```bash
python ~/.workbuddy/skills/ofd-reader/scripts/selftest.py     # 期望 21 项全 PASS
```

## Files

- `scripts/cli.py` — 命令行入口
- `scripts/selftest.py` — 合成 OFD 自检（21 项断言）
- `scripts/ofdreader/` — 解析库（`container` / `parser` / `resources` / `extract` / `validate` / `ns` / `model`）
- `references/pitfalls.md` — 真实文件踩坑清单（10 条，症状→根因→修法）
