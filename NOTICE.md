# NOTICE — 来源与版权说明

本仓库两个 skill 的许可状态不同，公开前请务必阅读本文件。

## `ofd-reader/` — MIT 许可

`ofd-reader/` 下的全部代码（解析器、CLI、自检脚本）为原创实现，
采用 MIT 许可，见仓库根目录 [LICENSE](LICENSE)。
零外部依赖，仅使用 Python 标准库。

## `ofd-standard/` — 学习性整理，**非官方发布物**

### 1. 章节笔记（原创性整理）

`chapters/ch01–ch15.md`、`cheatsheet.md`、`glossary.md`、`patterns.md`
—— 依据 **GB/T 33190—2016《电子文件存储与交换格式 版式文档》**
（中国国家标准化管理委员会发布）整理的结构化学习笔记、术语与速查表，
含大量转述、归纳与重构，并混入实现经验注解。

### 2. 附录 A 的 13 个 XSD（标准原文，另见 `schemas/README.md`）

这 13 个文件是 **GB/T 33190—2016 规范性附录 A 的原文**，
由本仓库自带的 `ofd-standard/tools/extract_appendix_xsd.py`
从标准 PDF 直接复原（该 PDF 的排版系统省略了 XML 标记内部的词间空格，
工具按 XSD 语法确定性重建，细节见 `schemas/README.md`）。

**校验（2026-09-11）**：

- 13/13 可被 lxml 编译为合法 `XMLSchema`（含 `xs:include` 解析）；
- 13/13 与社区转录版 [GreenYun/OFD-Schema](https://github.com/GreenYun/OFD-Schema)
  **去空白后逐字符一致** —— 两条完全独立的获取路径互为印证；
- 本版本额外保留了标准附录自带的 **31 条中文注释**。

SHA-256：

```
5327b087b4296cdf08086460a2cc979c36a5e2a7f28b3aacd36979cdc757ae70  Annotation.xsd
4fe84fb23d6d8d40ad7a1b2dc91bde8abdee715a39793e3cf2bbca8d65389a4a  Annotations.xsd
4b7573197fea25fe4d868a6b5c7b6ece9ec11f41f43b5869bb96e28b64fedec1  Attachments.xsd
22e7655afe1d450e9e207c5d8ea236c6740dcb28290d0da0a66416f920a81519  CustomTags.xsd
4d1ed609a699b16fe26cbabc4aa3ad91be9b4b0abbfdd856ab53aa7482fcc19b  Definitions.xsd
f566ac6501f7580582ac6fe7257d36ffe5f49f350ef3d9ce66cfdf29cac400c6  Document.xsd
9b3eebf7fa16ba56b0d4df789e2d5d08f6a308e59dc6c9fb18304ceb182c12f2  Extensions.xsd
d9c8b97270a9ae15a8be8740a1415766a84a163fa6a1b9d9019d45843e59ccfb  OFD.xsd
504298b10b211bbd0f23a128dbcdcc51e65ada6dca47f034adf50c0af978e27b  Page.xsd
31a3e51f74841bfc2214c2cddef1543bb891817e808f7f46e67599e3ea271543  Res.xsd
e5a21cf9ddd49d70fdd9915b3a695fae9bee11cb43fefd2bb19419d523aad10e  Signature.xsd
82a9ec968d30cbe07980a9075acc491fb1060dbc48f679b057045e3a914be5c0  Signatures.xsd
c0b4163ed124b3159db674a6f2aeb36657d14554d1841ccfc5eb8f4fd28397e4  Version.xsd
```

（文件为 LF 换行、UTF-8 无 BOM；由工具重新生成会得到相同结果。）

> **版权**：标准文本著作权属于发布机构，`GB/T` 为推荐性国家标准，
> 不等于可自由再分发。本仓库对这些文件不主张、也无法授予许可。


## 免责声明

`ofd-standard/` 内容用于学习与互操作实现参考，**不保证与标准原文完全一致**；
涉及合规判定时请以官方发布的标准原文为准。
