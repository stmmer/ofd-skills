# 真实 OFD 文件踩坑清单

在 WPS / 点聚 / 数科 产出的真实文件上验证得出。踩过的坑按"症状 → 根因 → 修法"记录。

## 1. `BaseLoc` / `ID` / `Title` 是属性，不是子元素

- **症状**：页列表为空、大纲标题为空、模板页找不到。
- **根因**：标准正文用「名称/类型/说明/备注」**平铺表格**描述结构 ——
  §7.6 表11「页树属性」把 `Page`、`ID`、`BaseLoc` 并排列成三行，
  元素与它的属性同表分行出现，**看起来像父子关系**，照抄就错。
  这是标准的表格体例，**不是 OCR 损坏**（2026-09-11 用数字版 PDF 核对确认）。
  附录 A 的 XSD 表述很明确：`<xs:element name="Page">` 内部是
  `<xs:attribute name="ID" type="ST_ID"/>` + `<xs:attribute name="BaseLoc" type="ST_Loc"/>`。
  真实文件里这些都是**属性**：`Page/@BaseLoc`、`Page/@ID`、`OutlineElem/@Title`、
  `TemplatePage/@ID|BaseLoc|ZOrder`、`Signature/@ID|BaseLoc|Type`。
- **修法**：一律先按属性读，属性缺失再退回子元素。

## 2. `os.path.join` 把盘符当盘相对路径

- **症状**：输出落到 `C:\f\OFDReader\...`。
- **根因**：传入 `/f/OFDReader/...`（Git-Bash 风格），Windows Python 视为盘相对路径。
- **修法**：一律传带盘符绝对路径 `F:/...`。容器解析内部用 `os.path.join` + `normpath`，
  不手工按分隔符切分（否则 `C:` 会被拆坏）。

## 3. `base_dir` 带前导 `/` 会让 `os.path.join` 丢掉包根

- **症状**：`SignValue.dat` 解析成 MISSING。
- **根因**：由绝对 loc `/Doc_0/Signs/Signatures.xml` 求 `dirname` 得 `/Doc_0/Signs`，
  `os.path.join(root, "/Doc_0/Signs")` 认为第二个参数是绝对路径 → 包根被整个丢弃。
- **修法**：`container.resolve()` 内对 `base_dir` 做 `lstrip("/")`。

## 4. 嵌套 ST_Loc 要相对"声明它的文件"解析

- **症状**：注释 0 条（`FileLoc` 解析到包根，找不到文件）。
- **根因**：`Annots/Page_1.xml` 应相对 `Annotations.xml` 所在目录（`Doc_0`）解析，
  但 `dirname("Annotations.xml")` 得空串 → 丢了 `Doc_0` 前缀。
- **修法**：用 `_ref_dir(loc, base_dir)` 统一计算声明文件所在目录：
  绝对 loc 取 `dirname(loc[1:])`，相对 loc 取 `dirname(join(base_dir, loc))`。

## 5. 资源路径相对文档目录，不是包根

- **症状**：图像抽不出来（0 张）。
- **根因**：`CommonData/PublicRes|DocumentRes` 是相对**文档目录**（`Doc_0`）的，
  资源文件真实路径还要再拼 `Res/@BaseLoc`。
- **修法**：res 路径拼 `Doc_0` 前缀；`MediaFile` 再拼 `BaseLoc`。

## 6. 模板页不展开会丢整层内容

- **症状**：缺红头、页眉、页脚、水印。
- **根因**：这些内容在 `CommonData/TemplatePage` 指向的模板页里，本页 `Content.xml` 没有。
  且引用是页对象内的 `<Template TemplateID ZOrder/>`（**不是** `Page/@TemplateID` 属性 ——
  `Document.xsd` 的 `Pages/Page` 只有 `ID` + `BaseLoc`）。
- **修法**：`load_page_content_expanded()` 返回
  `[Background 模板…, 本页, Foreground 模板…]`；嵌套模板递归展开 + visited 环检测。

## 7. 复合对象里看不到文字

- **症状**：页面上明明有字，抽出来是空的。
- **根因**：`CompositeObject` 只带 `ResourceID`，图元在
  `CompositeGraphicUnits/CompositeGraphicUnit/Content` 里。
- **修法**：按 `ResourceID` 查资源表展开内部 `Content`；`_expanding` 集合防自引用死循环。

## 8. 文本间距：固定 mm 阈值对 CJK + 数字太脆

- **症状**：`200 4 年`、`（三 ）` 这类被错误插入空格。
- **修法**：字形级坐标 + 间距阈值插空格，再用两条正则清理：
  - 数字后紧跟 CJK/数字/日期单位的空格 → 删除（还原 `2004年 8月 28日`）
  - 全角括号内侧空格 → 删除（`（三 ）` → `（三）`）

## 9. 严格 Schema 校验会误杀真实文件

- **症状**：对点聚/WPS 文件跑附录 A XSD，12 PASS / 4 FAIL。
- **根因**：真实文件普遍是 OFD **v1.1**（非 1.0）、数字型 `ST_ID`、
  厂商扩展元素（`CopyText`、`Provider/@OFDProMode`）、日期非 `xs:date` 零填充。
- **关键细节：标准附录 A 自己有 8 处把 ID 属性写成 `type="xs:ID"`**
  （`Attachments/@ID`、`Signature/@ID`、`Version/@ID` ×2、`Signatures/MaxSignId`、
  `Signatures/Signature/@ID`、`OFD/Versions/Version/@ID`）。
  而 `xs:ID` 要求 XML NCName（不能以数字开头），真实文件却写 `ID="1"` ——
  于是必然报 `'1' is not a valid value of the atomic type 'xs:ID'`。
  **这是标准自身的缺陷，不是转录错误**：同一套 Schema 里 `Definitions.xsd` 的
  `ST_ID` 定义是正确的 `xs:unsignedInt`。
- **勘误**：本清单早期版本称"GreenYun 转录版把 `ST_ID` 定义成 `xs:ID`" —— 这是**错的**。
  `Definitions.xsd` 中 `ST_ID = <xs:restriction base="xs:unsignedInt"/>`，
  与标准正文"无符号整数"**一致**；上述 `xs:ID` 是**内建类型**直接用在个别属性上，
  与 `ST_ID` 的定义无关。全套 XSD 已核对与标准附录 A 逐字符一致。
- 实测基线：点聚/WPS 文件跑附录 A 严格校验 = **12 PASS / 4 FAIL**（4 个失败即上面这类）。
- **修法**：**解析必须宽松**，schema 校验只作告警不拦截。内置 `lenient_check` 只报
  缺 `OFD.xml`、页 `BaseLoc` 不可解析、XML 非良构这类真问题。

## 10. Windows 上 Git-Bash 路径 / 编码

- 传给 Python 的路径统一用 `X:/...`；不要 `ls` 出来的 `/x/...`。
- 临时目录用 `tempfile.mkdtemp`，关闭时 `shutil.rmtree(ignore_errors=True)` 只删自己创建的目录。
- ZIP 解包做了 zip-slip 校验（拒绝逃逸出目标目录的成员），因技能会在别的机器上运行。
