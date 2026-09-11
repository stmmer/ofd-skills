# Chapter 5: 页树与页对象（§7.6–7.7）

## Core Idea
文档根节点的 `Pages` 是一棵**页树**：每个 `Page` 节点含 `ID` 与指向页描述文件 `BaseLoc`；页对象可引用**模板页**复用重复内容（页眉/页脚/水印等），解析渲染时必须先合并模板页再绘制本页内容。

## Frameworks Introduced
- **页树前序遍历定序**：一个页树可含多个 `Page` 节点，页顺序 = 对页树做前序遍历时叶节点的访问顺序。
  - When to use: 计算"第 N 页"时按前序遍历，而非目录顺序。
- **模板页复用**：重复出现的内容统一在模板页描述，普通页通过 `TemplateID` 引用，避免每页重复描述。
  - How: 渲染某页时，先绘制其引用模板页内容，再叠加本页 `Content`。

## Key Concepts
- **CT_Pages（页树）**：含 `Page` 子节点；`Page` 属性 `ID`(ST_ID,必选)、`BaseLoc`(ST_Loc 指向页对象描述文件,必选)。
- **页对象 Page**：含 `Area`(CT_PageArea)、`TemplateID`(ST_RefID 引用模板页)、`Content`(CT_PageBlock) 等。
- **模板页 TemplatePage**：结构与普通页相同，挂在文档根 `CommonData/TemplatePage`。
- **CT_PageBlock（页面块）**：可嵌套的页面内容容器，承载文字/图形/图像/复合/视频等图元。

## Mental Models
- 页树像**文件夹树**，叶子才是真实页；模板页像 CSS 父样式，被普通页继承。
- Think of `TemplateID` as a **base layer**：模板先画，本页内容后画覆盖其上。

## Anti-patterns
- **忽略模板页**：只渲染本页 Content 会得到缺页眉/水印的不完整页。
- **用目录序代替前序遍历**：嵌套页树下顺序以前序遍历为准。
- **模板页循环引用**：模板再引用模板需做环检测，防止死循环。

## Reference Tables

表11 页树属性

| 名称 | 类型 | 说明 |
|---|---|---|
| Page | CT_Page | 页节点，可多个；顺序=前序遍历叶节点顺序，必选 |
| ID | ST_ID | 页标识，不与已有重复，必选 |
| BaseLoc | ST_Loc | 指向页对象描述文件，必选 |

## Worked Example
页树与模板引用：
```xml
<ofd:Pages>
  <ofd:Page ID="1" BaseLoc="Pages/Page_0/Content.xml"/>
  <ofd:Page ID="2" BaseLoc="Pages/Page_1/Content.xml"/>
</ofd:Pages>
<!-- 页对象引用模板 -->
<ofd:Page Area="..." TemplateID="100">
  <ofd:Content>
    <ofd:PageBlock> ... </ofd:PageBlock>
  </ofd:Content>
</ofd:Page>
```

## Key Takeaways
1. 页顺序由页树前序遍历决定。
2. `Page` 必须有 `ID`（唯一）与 `BaseLoc`。
3. 渲染前先展开模板页 `TemplateID`，再叠加本页内容。
4. `CT_PageBlock` 是可嵌套的内容容器，图元都挂在它下面。

## Connects To
- **ch04**: 页树挂在文档根 `Pages`
- **ch06**: 页资源 `PageRes.xml` 在页对象中指定
- **ch07-ch10**: PageBlock 内图元（图形/图像/文字）的描述
