# Chapter 8: 图形（§9）

## Core Idea
图形由**路径对象 PathObject** 描述：用 `FigureSegment`（图元段）按移动/线段/贝塞尔曲线/圆弧组合出形状，再用填充规则与绘制参数上色。支持**非紧缩描述**（可读的图元段序列）。

## Frameworks Introduced
- **路径 = 图元段序列**：`CT_Path` 由若干 `FigureSegment` 组成，每段是 Move/Line/CubicBezier/Arc 之一。
  - When to use: 渲染任意矢量形状时，解析 FigureSegment 序列并在页面空间重绘。
- **填充规则 FillRule**：控制自交/嵌套路径的填充方式（非零绕数 / 奇偶规则，标准定义具体枚举）。
  - How: 光栅化前按 FillRule 决定像素归属。
- **非紧缩描述（§9.3）**：用 XML 子元素表达移动/线段/贝塞尔/圆弧，便于人工阅读与编辑。

## Key Concepts
- **图形对象 PathObject**：含 `Boundary`(ST_Box 外接矩形)、`CTM`、`FillColor`/`StrokeColor`/`FillRule`、以及图元段 `FigureSegment`。
- **移动 Move**：设置当前点，不绘制。
- **线段 Line**：从当前点到目标点画直线。
- **贝塞尔曲线 CubicBezier**：三次贝塞尔，控制点 + 终点。
- **圆弧 Arc**：按圆心/半径/起止角等参数描述弧段。
- **绘制参数**：线宽、连接样式（LineJoin）、端点样式（LineCap）、虚线（DashPattern）来自资源 DrawParam 或内联。

## Mental Models
- 路径像 **SVG 的 path d 属性**：一串命令（M/L/C/A）重建轮廓。
- Think of `FillRule` as the rule that decides **which enclosed regions get painted** for self-intersecting shapes.

## Anti-patterns
- **忽略 FillRule**：自交图形填错区域。
- **不先 Move**：图元段序列必须以移动起始，否则当前点未定义。
- **只看紧凑格式**：标准同时支持紧凑与 XML 非紧缩描述，解析需兼容两种。

## Reference Tables

图元段类型（§9.3）

| 段 | 含义 |
|---|---|
| Move | 移动当前点（不绘制） |
| Line | 当前点→目标点直线 |
| CubicBezier | 三次贝塞尔曲线 |
| Arc | 圆弧 |

绘制参数相关（§8.2）

| 项 | 说明 |
|---|---|
| 线连接样式 LineJoin | 线段连接处的处理 |
| 线条端点样式 LineCap | 线段端点的处理 |
| 虚线样式 DashPattern | 虚线 |
| 截断值 | 连接点截断阈值 |

## Worked Example
非紧缩描述一段线 + 贝塞尔：
```xml
<ofd:PathObject Boundary="0 0 100 100" FillRule="NonZero">
  <ofd:FigureSegment>
    <ofd:Move X="0" Y="0"/>
    <ofd:Line X="100" Y="0"/>
    <ofd:CubicBezier X1="50" Y1="80" X2="80" Y2="80" X="100" Y="100"/>
  </ofd:FigureSegment>
</ofd:PathObject>
```

## Key Takeaways
1. 图形 = PathObject + FigureSegment 序列。
2. 图元段四类：Move/Line/CubicBezier/Arc。
3. 填充规则决定自交区域着色。
4. 支持紧凑与 XML 非紧缩两种描述，解析需都兼容。
5. 线型/端点/虚线来自绘制参数。

## Connects To
- **ch07**: 图形在页面/对象空间绘制，用 CTM 与裁剪区
- **ch06**: 绘制参数/颜色空间是资源
- **ch09-ch10**: 图像与文字是并列图元
