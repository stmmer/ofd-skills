# OFD 速查 / 决策指南（GB/T 33190—2016）

面向 OFDReader 实现者的单页决策表。具体章节见各 `chapters/chNN-*.md`。

## 解析顺序（加载一个 OFD 的必做步骤）
1. ZIP 6.2.0 解包 → 找根 `OFD.xml`（名固定、唯一）。找不到即非法。
2. 读 `OFD.xml`：`Version`(=1.0)、`DocType`(OFD/OFDA)、`DocBody`→`DocRoot`(Document.xml)。
3. 读 `Document.xml`：取 `CommonData`(PageArea/PublicRes/DocumentRes/DefaultCS) 与 `Pages`。
4. 遍历页树（前序）取每页 `BaseLoc` → 页对象 → 先展开 `TemplateID` 模板页 → 再画本页 `Content`(PageBlock 图元)。
5. 图元引用资源时：页(PageRes)→文档(DocumentRes)→公共(PublicRes) 三级回退；相对路径基于 `BaseLoc`。

## 决策规则（if/then）
- **若**路径大小写不一致 → **则**视为不同资源（ST_Loc 区分大小写）。
- **若**遇到 `ST_RefID` = 0 → **则**当作无效引用，跳过该引用。
- **若**页对象有 `TemplateID` → **则**先渲染模板层再叠加本页（防缺页眉/水印）。
- **若** `DefaultCS` 缺失 → **则**默认 RGB 颜色空间。
- **若**资源三级都查不到 ID → **则**报错而非静默用错误资源。
- **若**遇到未知扩展节点 (CustomTags/Extensions) → **则**跳过、不崩溃（向前兼容）。
- **若**改了被签名范围的文件 → **则**必须重算摘要并刷新 `SignedValue.dat`，否则验真失败。
- **若** TIF 多媒体 → **则**取首页（TIF 不支持多页）。
- **若**文字无逐字坐标 → **则**用基准线 + Delta 沿排版方向定位，勿假设等距。

## OFD 元素 → 渲染管线映射
| 规范对象 | 渲染动作 |
|---|---|
| OFD.xml | 入口/版本/类型校验 |
| Document.xml / CommonData | 建立页面尺寸、默认颜色空间、资源注册表 |
| PageArea (4 Box) | 设裁剪链 Physical⊃Application⊃Content；Bleed 可外溢 |
| PageBlock | 递归容器，承载子图元 |
| PathObject | 重建 FigureSegment → 填充/描边（按 FillRule）|
| ImageObject | 按 ResourceID 取资源字节 → Boundary/CTM 绘制 → 裁剪 |
| TextObject | 加载 Font → 定位(逐字/基准线) → 字形变换 → 填充/描边 |
| CompositeObject | 展开内部图元后绘制 |
| DrawParam（资源） | 线宽/连接/端点/虚线/颜色 |
| Clip | 限制图元绘制范围 |
| Action | 路由交互（跳转/URI/附件/播放）|

## 离线校验（用内置 Schema）
- Schema 目录：`schemas/`（13 个附录 A XSD，已 lxml 校验通过，互相 include 仅本地文件，可离线）。
- 命令：`python validate.py <file.ofd>` 校验整个包；`python validate.py --selfcheck` 校验 Schema 本身。
- 自动按根元素名匹配：`<OFD>`→OFD.xsd、`<Document>`→Document.xsd、`<Page>`→Page.xsd、`<Res>`→Res.xsd、`<Annotations>`/`<Annotation>`、`<Signatures>`/`<Signature>`、`<CustomTags>`、`<Extensions>`、`<Attachments>`、`<Version>`(s)。
- 依赖 `lxml`（`pip install lxml`）。校验失败会逐文件列出 `PASS/FAIL/SKIP`。

## 阈值与默认值（实现直接用）
- 坐标单位：**毫米**；页面空间原点：**左上角**，X 右 / Y 下。
- `MaxUnitID` 初始 0，新增对象 = `MaxUnitID + 1`。
- 权限缺省：Edit/Annot/Export/Signature/Watermark/PrintScreen = true；Print 不限制份数。
- 视图缺省：`PageMode=None`、`PageLayout=OneColumn`、`ZoomMode=Default`。
- 底纹 `RelativeTo` 默认 Object；`ReflectMethod` 默认 Normal。
- `Copies` ≤0 表示打印份数不受限；`Copies=0` 禁止打印。

## 自测清单（一个 OFD 能否正确打开）
- [ ] ZIP 解包成功且含唯一 `OFD.xml`
- [ ] 命名空间 = `http://www.ofdspec.org/2016`（默认 ns）
- [ ] 所有 ST_Loc 大小写正确、ST_RefID 非 0 且存在
- [ ] 模板页已展开、四 Box 裁剪正确
- [ ] 坐标按毫米、CTM 变换正确
- [ ] 字型资源按作用域命中、字形变换全覆盖
- [ ] 签名范围文件摘要一致（如实现验真）

## 关键"味道"（识别问题）
- 页缺页眉/水印 → 多半没展开模板页。
- 内容被截断 → 多半四 Box/裁剪区处理反了。
- 字体错乱 → 资源作用域查错或字形变换假设 1:1。
- 打开即崩 → 遇到未知扩展未优雅跳过。
