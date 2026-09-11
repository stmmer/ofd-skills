# Chapter 4: 基本结构（§7）

## Core Idea
OFD 所有内容都是带命名空间的 XML。掌握主入口 `OFD.xml`、文档元数据 `CT_DocInfo`、文档根节点、公共数据 `CommonData` 与页面区域 `PageArea` 五层结构，就掌握了 OFD 的骨架。

## Frameworks Introduced
- **命名空间固定**：所有 XML 使用 `http://www.ofdspec.org/2016`，根节点声明 `xmlns="ofd"`（默认命名空间），元素用 `ofd:` 前缀，元素属性不使用命名空间前缀。
- **字符编码**：OFD 文件应支持 GB 18030 与 GB 13000。
- **6 种基础数据类型**（表2）：`ST_Loc`、`ST_Array`、`ST_ID`、`ST_RefID`、`ST_Pos`、`ST_Box`。
  - When to use: 所有路径/坐标/标识属性都使用这些类型，解析器需先实现它们。

## Key Concepts
- **ST_Loc**：包内文件路径。规则：`/` 为根；未显式指定代表当前路径；`..` 为父路径；路径区分大小写。
- **ST_Array**：数组，元素以空格分隔，不可嵌套（元素可为除 ST_Loc/ST_Array 外的类型）。
- **ST_ID**：标识，无符号整数，文档内唯一，0 表示无效标识。
- **ST_RefID**：标识引用，无符号整数，必须引用文档内已定义的 ST_ID。
- **ST_Pos**：点坐标，`x y` 空格分隔，可整可浮。
- **ST_Box**：矩形区域，`x y w h` 空格分隔，前两个为左上角坐标，后两个为宽高（须 > 0）。
- **CT_DocInfo**：文档元数据（DocID、Title、Author、Subject、Abstract、CreationDate、ModDate、DocUsage、Cover、Keywords、Creator、CreatorVersion、CustomDatas）。
- **CT_PageArea**：页面区域，含 PhysicalBox / ApplicationBox / ContentBox / BleedBox。
- **CT_Permission**：文档权限声明（防扩散）。
- **CT_VPreferences**：视图首选项。

## Mental Models
- `OFD.xml` → `DocBody` → `DocRoot`(Document.xml) → `CommonData`+`Pages` 是一条**单向引用链**。
- Think of `ST_ID`/`ST_RefID` as **primary key / foreign key**：对象用 ST_ID 注册，别处用 ST_RefID 引用。
- 页面区域四 Box 是**嵌套裁剪关系**：Physical ⊃ Application ⊃ Content；Bleed 可超出 Physical。

## Anti-patterns
- **路径大小写不敏感假设**：ST_Loc 明确区分大小写，比较/查找时勿做大小写归一。
- **硬编码命名空间前缀**：标准用默认命名空间（`xmlns="ofd"`），解析应支持默认 ns，而非固定 `ofd:`。
- **忽略 0 = 无效标识**：ST_ID/ST_RefID 中 0 表示无效，引用前需判 0。

## Reference Tables

表2 基础数据类型

| 类型 | 说明 | 示例 |
|---|---|---|
| ST_Loc | 包内文件路径，`/`根、`.`当前、`..`父，区分大小写 | `Pages/Page_0/Content.xml` |
| ST_Array | 空格分隔数组，不可嵌套 | `2.0 0 0 2.0` |
| ST_ID | 无符号整数标识，文档内唯一，0 无效 | `100` |
| ST_RefID | 引用已定义 ST_ID | `1000` |
| ST_Pos | `x y` 点坐标 | `10 10` |
| ST_Box | `x y w h` 矩形，w/h>0 | `10 10 50 50` |

表3 OFD 主入口属性（`OFD.xml`）

| 名称 | 类型 | 说明 |
|---|---|---|
| Version | xs:string | 格式版本号，取值 `1.0`，必选 |
| DocType | xs:string | `OFD` 或 `OFDA`（存档规范），必选 |
| DocBody | CT_DocBody | 文档体入口，可多个，必选 |
| DocInfo | CT_DocInfo | 元数据，必选 |
| DocRoot | ST_Loc | 指向文档根节点 Document.xml，可选 |
| Versions | — | 版本描述节点，见第19章，可选 |
| Signatures | ST_Loc | 指向签名结构，见第18章，可选 |

表7 页面区域属性（CT_PageArea）

| 名称 | 说明 |
|---|---|
| PhysicalBox | 页面物理区域，左上角为页面空间原点，必选 |
| ApplicationBox | 显示区域（页眉/页脚/版心），位于物理区域内 |
| ContentBox | 版心区域，位于显示区域内 |
| BleedBox | 出血区域，可超出物理区域，缺省=物理区域 |

## Worked Example
最小 `OFD.xml` 主入口：
```xml
<?xml version="1.0" encoding="GB18030"?>
<ofd:OFD xmlns="ofd" Version="1.0" DocType="OFD">
  <ofd:DocBody>
    <ofd:DocInfo>
      <ofd:DocID>00000000000000000000000000000001</ofd:DocID>
      <ofd:Title>示例文档</ofd:Title>
    </ofd:DocInfo>
    <ofd:DocRoot>Doc_0/Document.xml</ofd:DocRoot>
  </ofd:DocBody>
</ofd:OFD>
```

## Key Takeaways
1. 全部 XML 命名空间固定为 `http://www.ofdspec.org/2016`，用默认 ns。
2. 先实现 6 种基础数据类型，尤其 ST_Loc（大小写敏感）与 ST_ID/ST_RefID（0=无效）。
3. `OFD.xml` → DocBody → DocRoot 是加载主链。
4. 页面四 Box 为嵌套裁剪关系，渲染时按层裁剪。
5. 权限与视图首选项挂在文档根节点，控制防扩散与初始视图。

## Connects To
- **ch03**: 容器与文件组织
- **ch05**: 页树/页对象挂在文档根 `Pages`
- **ch06**: 资源与大纲挂在文档根
- **ch15**: 各类型 Schema 见附录 A
