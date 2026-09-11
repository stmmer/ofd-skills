# Chapter 13: 自定义标引与扩展信息（§16–17）

## Core Idea
OFD 预留两类扩展机制：**自定义标引（CustomTags）** 用于给文档添加语义结构/标签（便于检索与无障碍），**扩展信息（Extensions）** 用于厂商在标准之外挂载私有数据。两者都通过文档根的 `ST_Loc` 引用独立的列表文件，保证向前兼容。

## Frameworks Introduced
- **自定义标引 CustomTags（§16）**：文档级标签体系，描述语义结构（如标题/章节/图表），可被视图首选项 `UseCustomTags` 呈现。
  - When to use: 做文档语义导航、全文检索、无障碍阅读时读取。
- **扩展信息 Extensions（§17）**：厂商扩展数据容器，标准未定义其内容，由实现自行解释。
  - How: 解析器应忽略不认识的扩展，保持健壮性。

## Key Concepts
- **CustomTags 列表文件**：文档根 `CustomTags`(ST_Loc) 指向；内部为标签树/集合。
- **Extensions 列表文件**：文档根 `Extensions`(ST_Loc) 指向；存放私有扩展。
- **向前兼容原则**：标准允许扩展，但核心解析不应因未知扩展而失败。

## Mental Models
- 自定义标引像 **文档的语义大纲/标签云**；扩展信息像 **厂商私有命名空间**。
- Think of Extensions as a **graceful-ignore zone**: known fields parsed, unknown skipped.

## Anti-patterns
- **因未知扩展崩溃**：解析器必须容忍并跳过不识别的扩展节点。
- **把标引当布局依赖**：CustomTags 是语义层，不应影响版式渲染。

## Reference Tables

文档根扩展引用

| 节点 | 指向 |
|---|---|
| CustomTags (ST_Loc) | 自定义标引列表文件（§16） |
| Extensions (ST_Loc) | 扩展信息列表文件（§17） |

## Key Takeaways
1. 自定义标引提供语义结构，利于检索/导航/无障碍。
2. 扩展信息容纳厂商私有数据，应优雅忽略未知项。
3. 两者都通过文档根 ST_Loc 引用独立文件。
4. 扩展不得破坏核心解析的向前兼容。

## Connects To
- **ch04**: 文档根 CustomTags/Extensions 节点
- **ch04 VPreferences**: `UseCustomTags` 可呈现语义结构
