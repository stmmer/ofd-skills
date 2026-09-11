# Chapter 15: 附录 Schema（规范性附录 A）

## Core Idea
标准的规范性附录 A 给出所有 XML 的 **XSD Schema**，是实现与校验 OFD 文件的权威契约。每个主要 XML 文件对应一个或多个 `.xsd`，解析器应基于这些 Schema 做结构校验。

## Frameworks Introduced
- **Schema 即契约**：所有 OFD XML 的结构、元素、属性、类型都由附录 A 的 XSD 定义；实现与第三方校验都以它为基准。
  - When to use: 构建/校验 OFD 文件时，用对应 XSD 做 XSD 校验，而非只做宽松解析。

## Key Concepts
- **命名空间**：Schema 目标命名空间 `http://www.ofdspec.org/2016`，与 §7.1 一致。
- **核心 Schema 文件**（附录 A 列出）：
  - `OFD.xsd` — 主入口结构（见 §7.4）
  - `Document.xsd` — 文档根节点（见 §7.5）
  - `Annotations.xsd` / `Annotation.xsd` — 注释（见 §15）
  - `Res.xsd` — 资源文件（见 §7.9）
  - `Extensions.xsd` — 扩展信息（见 §17）
  - `Attachments.xsd` — 附件（见 §20）
  - （以及 Page/Text/Image/Path/Signature 等子结构 Schema）
- **CT_* 类型**：标准以下划线前缀 `CT_` 表示复杂类型（如 `CT_DocInfo`、`CT_PageArea`、`CT_Text`、`CT_Image`、`CT_Path`、`CT_Permission`、`CT_VPreferences`），`ST_*` 表示基础类型（§7.3）。
- **派生方式**：许多元素 `derivedBy extension`，在基础类型上扩展 `ID` 等属性。

## Mental Models
- 附录 A 的 XSD 是 **OFD 的类型定义文件集**，等价于代码的接口/类定义。
- Think of `CT_` as **class**, `ST_` as **primitive type**.

## Anti-patterns
- **只做宽松解析不校验**：应至少对关键文件做 XSD 校验，捕获结构错误。
- **混淆 CT_/ST_ 含义**：CT_ = 复杂类型（元素），ST_ = 简单基础类型（属性值）。

## Reference Tables

主要 Schema 文件映射

| XSD | 对应内容 |
|---|---|
| OFD.xsd | 主入口 OFD.xml（§7.4） |
| Document.xsd | 文档根节点 Document.xml（§7.5） |
| Res.xsd | 资源文件（§7.9） |
| Annotations.xsd / Annotation.xsd | 注释（§15） |
| Extensions.xsd | 扩展信息（§17） |
| Attachments.xsd | 附件（§20） |

## Key Takeaways
1. 附录 A 的 XSD 是实现的权威契约，优先按其校验。
2. `CT_` 复杂类型 / `ST_` 基础类型命名约定贯穿全文。
3. 各主要 XML 都有对应 Schema 文件。
4. 元素多用 `derivedBy extension` 扩展 ID 属性。

## Connects To
- **ch04**: ST_ 基础类型与 CT_ 复杂类型定义
- **ch03**: 各 XML 文件在容器中的位置
- **全章**: 每章结构均可在对应 XSD 找到定义
