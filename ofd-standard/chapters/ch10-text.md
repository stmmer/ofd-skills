# Chapter 10: 文字（§11）

## Core Idea
文字由**文字对象 TextObject（CT_Text）** 描述：引用字型资源，用文本串 + 定位描述（字符坐标或基准线）+ 可选的字形变换矩阵渲染。是版式文档"所见即所得"的核心，解析器必须正确处理字型引用与文字定位。

## Frameworks Introduced
- **字型资源 Font**：文字对象通过 `Font` 引用资源中定义的字型（`CT_Font`），字型可内嵌或引用外部字体文件。
  - When to use: 渲染文字前按 Font 资源 ID 加载字形轮廓/度量。
- **文字定位（§11.3）**：支持两种定位方式——按字符逐个给出坐标，或给出基准线（如基线/中线）后沿排版方向排列。
  - How: `TextCode` 的 `X`/`Y` 属性提供逐字坐标；否则用 `Body`/基准线 + Delta 数组。
- **字形变换（§11.4）**：映射关系分一对一、多对一、一对多、多对多，描述 Unicode 码点与字型中字形索引的对应。
  - When to use: 处理合字（ligature）、变体字形、CJK 多字形组合时。

## Key Concepts
- **CT_Text（TextObject）**：含 `Boundary`、`CTM`、`Font`(ST_RefID)、`Size`(字号)、`FillColor`、`TextCode`(文本串与坐标)、`StrokeColor`/`Stroke`(勾边)、`HScale`/`Weight` 等。
- **字型 Font**：在资源 `Fonts` 中定义，扩展 ID(ST_ID) 属性；可嵌入字体子集。
- **文字对象属性**：字间距、行距、字重、横向缩放、是否勾边等。
- **字形变换四种**：一对一（1:1）、多对一（多个码点→一个字形，如连字）、一对多（一个码点→多个字形，如组合字符）、多对多。

## Mental Models
- 文字对象像 **PDF 的 text show operator**：先设字体/字号/矩阵，再输出字形序列。
- Think of `TextCode` as a **positioned glyph run**: each run carries its own coordinates or a baseline.

## Anti-patterns
- **忽略字型引用作用域**：Font 资源在三级资源中，按作用域查找。
- **逐字等宽假设**：文字定位可能逐字给坐标，也可能是基准线 + Delta，勿假设等距。
- **字形 1:1 假设**：存在多对一/一对多/多对多变换，尤其 CJK 与连字。

## Reference Tables

文字对象关键属性（节选）

| 名称 | 说明 |
|---|---|
| Font | 引用字型资源 ID，必选 |
| Size | 字号 |
| Boundary | 文字外接矩形 |
| CTM | 变换矩阵 |
| TextCode | 文本串及定位（X/Y 或 Body+Delta） |
| FillColor / StrokeColor | 填充/勾边颜色 |
| HScale / Weight | 横向缩放、字重 |

字形变换类型（§11.4）

| 类型 | 含义 |
|---|---|
| 一对一 | 一个码点对应一个字形 |
| 多对一 | 多个码点→一个字形（连字） |
| 一对多 | 一个码点→多个字形（组合字符） |
| 多对多 | 多码点→多字形 |

## Worked Example
逐字坐标的文字对象：
```xml
<ofd:TextObject Font="10" Size="10.5">
  <ofd:TextCode X="30 45 60" Y="40 40 40">示例</ofd:TextCode>
</ofd:TextObject>
```

## Key Takeaways
1. 文字对象引用字型资源（三级作用域）。
2. 文字定位支持逐字坐标或基准线 + Delta。
3. 字形变换有 4 种映射，勿假设 1:1。
4. 支持填充、勾边、横向缩放、字重等。

## Connects To
- **ch06**: 字型是资源类型，在 Fonts 中定义
- **ch07**: 文字在页面空间用 CTM 绘制
- **ch05**: TextObject 是 PageBlock 子图元
