# OFD 实现模式与技巧（GB/T 33190—2016）

## 容器加载模式
**When to use**: 任何读/写 OFD 的入口。
**How**: 先 ZIP 解包（ZIP 6.2.0）→ 定位根 `OFD.xml`（文件名固定、唯一）→ 解析 `DocBody` → 按 `DocRoot` 加载 `Document.xml`。
**Trade-offs**: 不能直接流读字节；必须全量或按需解包后解析 XML。

## 资源作用域解析模式
**When to use**: 图元引用字型/颜色空间/绘制参数/图像/多媒体时。
**How**: 按 页资源(PageRes) → 文档资源(DocumentRes) → 公共资源(PublicRes) 顺序向上查找 ST_RefID；相对路径基于资源文件 `BaseLoc` 解析。
**Trade-offs**: 就近覆盖可减少重复定义，但查找需三级回退，注意作用域边界。

## 模板页展开模式
**When to use**: 渲染含 `TemplateID` 的页对象。
**How**: 渲染本页 Content 前，先绘制其引用的模板页内容；做模板引用环检测防止死循环。
**Trade-offs**: 减少重复描述（页眉/水印），但渲染需两遍合成。

## 坐标空间变换模式
**When to use**: 所有图元绘制。
**How**: 页面空间（左上原点、毫米）→ 用 CTM 变换到对象空间（图元外接矩形左上原点）→ 输出时按设备分辨率换算到像素。
**Trade-offs**: 与设备无关、可无损缩放；渲染管线需维护 CTM 栈。

## 路径重建模式
**When to use**: 处理 PathObject 矢量图形。
**How**: 顺序解析 FigureSegment（Move/Line/CubicBezier/Arc），维护当前点；按 FillRule 决定自交区域填充；兼容紧凑与 XML 非紧缩两种描述。
**Trade-offs**: 类似 SVG path，易于光栅化；需正确处理 FillRule 与段起始。

## 文字定位模式
**When to use**: 渲染 TextObject。
**How**: 按 `Font` 资源加载字型 → 用 TextCode 的逐字 (X,Y) 或 基准线+Delta 定位 → 应用字形变换（1:1/多对1/1:多/多对多）。
**Trade-offs**: 支持精细版式；CJK 与连字需字形变换映射，不能假设等宽。

## 签名验真模式
**When to use**: 校验文档完整性/身份。
**How**: 读 `Signs/Signatures.xml` → 对每个 `Sign_N` 按 `Signature.xml` 声明的签名范围计算文件摘要 → 与 `SignedValue.dat` 比对；外观由 Signature.xml 描述。
**Trade-offs**: 与内容分离便于并行校验；改动内容必须重算摘要否则失效。

## 扩展兼容模式
**When to use**: 解析含 CustomTags/Extensions 的文件。
**How**: 识别已知节点并解析，对未知扩展节点跳过（graceful ignore），保持向前兼容。
**Trade-offs**: 保证健壮性；厂商私有数据除非实现支持否则忽略。

## Schema 校验模式
**When to use**: 生成或校验 OFD 文件。
**How**: 用附录 A 对应 XSD（OFD.xsd/Document.xsd/Res.xsd/...）做 XSD 校验，而非只宽松解析。
**Trade-offs**: 捕获结构错误；需维护 Schema 文件集合。
