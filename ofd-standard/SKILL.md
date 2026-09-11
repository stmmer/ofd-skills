---
name: ofd-standard
description: "Knowledge base from \"GB/T 33190—2016 电子文件存储与交换格式（版式文档）\" by 中国国家标准化管理委员会. Use when implementing/parsing/validating OFD files (ZIP container, OFD.xml, Document.xml, page tree, coordinate system, PathObject/ImageObject/TextObject, resources, digital signature), or building an OFD reader/renderer."
---

<!-- argument-hint: [topic, element name, or chapter number, e.g. container, TextObject, signature, ch07] -->

# GB/T 33190—2016 电子文件存储与交换格式（版式文档 / OFD）
**Author**: 中国国家标准化管理委员会 | **Pages**: 132 | **Chapters**: 15 (mapped from §1–§20 + 附录A) | **Source**: 数字版 PDF（含完整文字层）| **Verified**: 2026-09-11

> OFD 是中国的版式文档国家标准，定位类似 PDF：版面固定、所见即所得、自包含、可长期保存与交换。
>
> **配套执行器**：需要真的把一个 `.ofd` 文件解析/抽取出来时，用 `ofd-reader` skill
> （纯标准库解析器，本 skill 提供契约基准）。

## How to Use This Skill

- **Without arguments** — load core frameworks for reference
- **With a topic** — ask about `container`, `TextObject`, `signature`, `坐标系统`, etc.; I find and read the relevant chapter
- **With chapter** — ask for `ch07`; I load that specific chapter
- **Browse** — ask "what chapters do you have?" to see the full index

When you ask about a topic not in Core Frameworks below, I will read the relevant chapter file before answering.

---

## Core Frameworks & Mental Models

**1. 容器即 ZIP（§6）** — OFD 文件 = 一个 ZIP 6.2.0 包。包内**唯一且文件名固定**的 `OFD.xml` 是主入口，解析第一步永远是解包 ZIP 再读它。其余 XML 与资源按目录层次组织：`Doc_N/Document.xml`、`Pages/Page_N/Content.xml`、`Res/PublicRes.xml`、`Signs/`。读取顺序：`ZIP 解包 → OFD.xml → DocBody → DocRoot(Document.xml) → Pages`。

**2. 命名空间与编码（§7.1–7.2）** — 所有 XML 命名空间固定 `http://www.ofdspec.org/2016`，根节点声明默认命名空间 `xmlns="ofd"`，元素用 `ofd:` 前缀、属性不用前缀。编码支持 GB 18030 / GB 13000。**切勿**对命名空间前缀或 ST_Loc 路径做大小写归一。

**3. 六基础数据类型（§7.3）** — `ST_Loc`(包内路径，`/`根、`.`当前、`..`父、区分大小写)、`ST_Array`(空格数组，不可嵌套)、`ST_ID`(无符号整数、文档内唯一、**0=无效**)、`ST_RefID`(引用已定义 ST_ID)、`ST_Pos`(`x y`)、`ST_Box`(`x y w h`，w/h>0)。实现解析器先落地这六种。

**4. 主入口 → 文档根引用链（§7.4–7.5）** — `OFD.xml`(Version=1.0, DocType=OFD/OFDA) → `DocBody` → `DocRoot`(Document.xml)。文档根节点含 `CommonData`(MaxUnitID/PageArea/PublicRes/DocumentRes/DefaultCS)、`Pages`(页树)、`Outlines`、`Permissions`、`VPreferences`、`Bookmarks`、`Attachments`、`Annotations`、`CustomTags`、`Extensions`、`Actions`。

**5. 页面四 Box 嵌套裁剪（§7.5）** — `PhysicalBox`⊃`ApplicationBox`(显示)⊃`ContentBox`(版心)；`BleedBox` 可超出物理区。渲染时按此层裁剪；超出部分忽略。

**6. 三级资源作用域（§7.9）** — 资源（字型/颜色空间/绘制参数/矢量图像/多媒体）按 页(PageRes)→文档(DocumentRes)→公共(PublicRes) **由内到外**查找；相对路径基于资源文件 `BaseLoc`。资源实际文件在容器目录，索引在 Res XML。

**7. 三类坐标空间（§8.1）** — 设备空间(输出相关)、页面空间(**左上原点、X 右、Y 下、毫米**)、对象空间(图元外接矩形左上原点)。图元先经 `Boundary` 平移进对象空间，再用 CTM 变换、按裁剪区绘制；坐标统一毫米，像素换算推迟到输出。

**8. 图元三件套（§9–11）** — `PathObject`(FigureSegment: Move/Line/CubicBezier/Arc + FillRule)、`ImageObject`(ResourceID 引用 + Boundary/CTM)、`TextObject`(Font 引用 + 逐字坐标或基准线定位 + 字形变换 1:1/多对1/1:多/多对多)。都挂在 `PageBlock` 下，可嵌套。

**9. 模板页复用（§7.7）** — 页对象内的 `Template` 子节点以 `@TemplateID` 引用模板页（`@ZOrder` 控层级，默认 `Background`），渲染时**先画模板层再叠加本页**，防缺页眉/水印；需做模板引用环检测。注意模板页是 `CommonData/TemplatePage` 的**属性** `ID`/`BaseLoc`，且引用**不在** `Page` 元素上（`Page` 只有 `ID`+`BaseLoc`）。

**10. 签名三件套（§18）** — `Signs/Signatures.xml`(列表) + `Sign_N/Signature.xml`(范围/外观) + `Seal.esl`(印章) + `SignedValue.dat`(值)。验真按签名范围算摘要比对 SignedValue；改内容须重算。

**11. 扩展兼容（§16–17）** — `CustomTags`(语义结构)、`Extensions`(厂商私有) 都经文档根 ST_Loc 引用；解析器须**优雅跳过未知扩展**保持向前兼容。

**12. Schema 即契约（附录A）** — 所有 XML 结构由 XSD 定义（`CT_`=复杂类型、`ST_`=基础类型）；生成/校验优先用对应 XSD（OFD.xsd/Document.xsd/Res.xsd/...）。

---

## Bundled Schemas（附录 A 离线校验）
本 skill 在 `schemas/` 目录内置了 GB/T 33190—2016 附录 A 的**全部 13 个 XSD**：`OFD.xsd`、`Document.xsd`、`Definitions.xsd`、`Page.xsd`、`Res.xsd`、`Annotations.xsd`、`Annotation.xsd`、`Signatures.xsd`、`Signature.xsd`、`CustomTags.xsd`、`Extensions.xsd`、`Attachments.xsd`、`Version.xsd`。它们均经 lxml 校验为合法 Schema，且彼此 `include` 仅指向本地文件，可**完全离线**使用。

> **来源（2026-09-11 起）**：这 13 个 XSD 是 GB/T 33190—2016 **规范性附录 A 的原文**，
> 由本 skill 自带的 `tools/extract_appendix_xsd.py` 从标准 PDF 确定性复原
> —— 生成过程**不依赖任何第三方转录版本**。
>
> **校验**：13/13 可被 lxml 编译为合法 `XMLSchema`；且与社区转录版
> [GreenYun/OFD-Schema](https://github.com/GreenYun/OFD-Schema) **去空白后逐字符一致**
> （39844 字符，0 处差异）。两条获取路径完全独立，互为印证。
> 本版本额外保留了标准附录自带的 **31 条中文注释**。
>
> **勘误**：本 skill 早期版本称"附录 A 的 XSD 文本 OCR 损坏严重、无法直接复用"
> 并因此改用第三方转录版。该结论只对**旧 OCR 版 PDF** 成立；
> 换成数字版 PDF（132 页、含完整文字层）后，附录 A 可完整复原 —— 上述工具即为证据。
>
> **版权**：标准文本著作权属于发布机构，`GB/T` 为推荐性国家标准，不等于可自由再分发；
> 本仓库对这些文件不主张、也无法授予许可。详见 [schemas/README.md](schemas/README.md)
> 与仓库根目录 `NOTICE.md`。

配套 `validate.py` 对 `.ofd` 包或解压目录做离线结构校验：
```bash
python validate.py document.ofd     # 校验包内全部 XML（按根元素名自动匹配 Schema）
python validate.py --selfcheck      # 校验内置 Schema 本身
```
需要 `lxml`（`pip install lxml`）。

## Chapter Index

| # | Title | Key Frameworks |
|---|-------|----------------|
| [ch01](chapters/ch01-scope-terms.md) | 范围、引用文件与术语（§1–4） | 版式文档定位 |
| [ch02](chapters/ch02-overview.md) | 概述（§5） | 自包含容器、成像模型、扩展名 .ofd |
| [ch03](chapters/ch03-container.md) | 文件结构（§6） | ZIP 容器、OFD.xml 主入口、文件层次 |
| [ch04](chapters/ch04-basic-structure.md) | 基本结构（§7） | 命名空间、6 基础类型、主入口、DocInfo、文档根、PageArea、权限、视图 |
| [ch05](chapters/ch05-page-tree-object.md) | 页树与页对象（§7.6–7.7） | 前序遍历定序、模板页复用 |
| [ch06](chapters/ch06-outline-resources.md) | 大纲与资源（§7.8–7.9） | 两级资源作用域、BaseLoc、资源类型 |
| [ch07](chapters/ch07-coordinate-system.md) | 页面描述（§8） | 三类坐标空间、CTM、颜色/底纹/渐变、裁剪区 |
| [ch08](chapters/ch08-graphics.md) | 图形（§9） | PathObject、FigureSegment、FillRule |
| [ch09](chapters/ch09-image.md) | 图像（§10） | ImageObject、资源引用、定位 |
| [ch10](chapters/ch10-text.md) | 文字（§11） | TextObject、字型、文字定位、字形变换 |
| [ch11](chapters/ch11-media-composite-actions.md) | 视频/复合/动作（§12–14） | 复合对象、五类动作 |
| [ch12](chapters/ch12-annotations.md) | 注释（§15） | 入口+分页两级注释 |
| [ch13](chapters/ch13-custom-extensions.md) | 自定义标引与扩展（§16–17） | CustomTags、Extensions、向前兼容 |
| [ch14](chapters/ch14-signature-version-attach.md) | 签名/版本/附件（§18–20） | 签名三件套、版本、附件 |
| [ch15](chapters/ch15-schema-appendix.md) | 附录 Schema（A） | XSD 契约、CT_/ST_ 命名 |

## Topic Index

- **容器 / ZIP / OFD.xml** → ch03
- **命名空间 / 编码** → ch04
- **基础类型 ST_Loc/ST_ID/ST_Box** → ch04
- **主入口 / DocInfo / 文档根** → ch04
- **页面区域 PageArea / 四 Box** → ch04
- **权限 Permissions / 视图 VPreferences** → ch04
- **页树 / 页对象 / 模板页** → ch05
- **大纲 Outline** → ch06
- **资源 Resources / 作用域 / BaseLoc** → ch06
- **坐标系统 / CTM / 对象空间** → ch07
- **颜色 / 底纹 / 渐变 / 裁剪区** → ch07
- **图形 PathObject / FillRule** → ch08
- **图像 ImageObject** → ch09
- **文字 TextObject / 字型 / 字形变换** → ch10
- **视频 / 复合对象 / 动作 Action** → ch11
- **注释 Annotations** → ch12
- **自定义标引 / 扩展 CustomTags/Extensions** → ch13
- **数字签名 Signature / 版本 / 附件** → ch14
- **Schema / XSD / CT_/ST_** → ch15, ch04

## Supporting Files

- [schemas/](schemas/) — 附录 A 全部 13 个 XSD（从标准 PDF 附录 A 复原；13/13 可编译，且与社区转录版逐字符一致。见 [schemas/README.md](schemas/README.md)）
- [validate.py](validate.py) — 离线校验脚本：对 `.ofd` 包或解压目录按根元素名匹配 Schema 校验
- [tools/extract_appendix_xsd.py](tools/extract_appendix_xsd.py) — 从标准 PDF 复原 `schemas/` 的工具（自包含，可重生成 / 校验）
- [glossary.md](glossary.md) — 全部关键术语与定义
- [patterns.md](patterns.md) — 实现模式与技巧（容器加载、资源解析、模板展开、坐标变换、签名验真等）
- [cheatsheet.md](cheatsheet.md) — 解析顺序、决策规则、OFD→渲染管线映射、自测清单（面向 OFDReader）

---

## Scope & Limits

本 skill 覆盖 GB/T 33190—2016 标准内容（结构、容器、页面描述、图元、资源、签名等）。来源为**数字版 PDF**（132 页，含完整文字层），章节内容据提取文本与标准结构综合提炼，并于 2026-09-11 逐条复核；具体数值/枚举以附录 A 的 XSD 与原文为准。实现落地请结合项目代码与附录 Schema 校验。

`schemas/` 内的 13 个 XSD 为 GB/T 33190—2016 规范性附录 A 的原文，由 `tools/extract_appendix_xsd.py` 从标准 PDF 确定性复原：13/13 可编译为合法 Schema，且与社区转录版 GreenYun/OFD-Schema 去空白后**逐字符一致**（两条独立路径互为印证），并保留了标准自带的 31 条中文注释。标准文本著作权属发布机构，本仓库不主张、也无法授予许可；仅供本地离线校验，勿对外公开分发。详见 [schemas/README.md](schemas/README.md)。
