# Chapter 12: 注释（§15）

## Core Idea
注释是附加在页面上、与正文内容分离的可交互层（批注、链接、高亮等）。结构上由**注释入口文件**（文档级索引）与**分页注释文件**（每页注释）两级组成，文档根通过 `Annotations`(ST_Loc) 指向入口。

## Frameworks Introduced
- **两级注释组织**：入口文件（`Annotations.xml`）列出各页注释文件位置；每页一个注释文件，挂在该页下。
  - When to use: 加载某页注释时，先读入口找到对应分页文件，再渲染该页注释。

## Key Concepts
- **注释入口文件（§15.1）**：索引各分页注释文件（按页关联）。
- **分页注释文件（§15.2）**：包含该页的注释集合，注释可含外观（Appearance）、动作、边界框等。
- **注释属性**：边界 `Boundary`、类型、内容、关联动作（见 §14）、外观描述。
- **文档根引用**：文档根节点 `Annotations`(ST_Loc) 指向注释列表文件。

## Mental Models
- 注释像 **PDF 的 annots**：独立层，可带外观与动作。
- Think of 入口文件 as a **manifest** that maps pages → their annotation files.

## Anti-patterns
- **把注释当正文渲染**：注释是可开关/可交互层，应与 PageBlock 内容分离处理。
- **忽略分页组织**：注释按页分文件，别假设单文件全量。

## Reference Tables

注释结构

| 文件 | 作用 |
|---|---|
| Annotations.xml（入口） | 文档级注释索引，关联各页注释文件 |
| Page_N 注释文件 | 该页注释集合 |

## Key Takeaways
1. 注释是独立可交互层，分入口 + 分页两级。
2. 文档根 `Annotations` 指向入口文件。
3. 注释可带动作与外观。
4. 渲染时按页加载对应注释文件。

## Connects To
- **ch04**: 文档根 `Annotations` 节点
- **ch11**: 注释可携带动作
- **ch15**: Annotations.xsd / Annotation.xsd 见附录 A
