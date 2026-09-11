# Chapter 6: 大纲与资源（§7.8–7.9）

## Core Idea
**大纲**是文档的树状导航结构；**资源**是绘制图元所需数据的集合（字型/颜色空间/绘制参数/矢量图像/多媒体），其实际文件存于容器特定文件夹，索引信息存于资源文件。资源分**公共资源**（文档根指定）与**页资源**（页对象指定）两级作用域。

## Frameworks Introduced
- **资源两级作用域**：公共资源（`PublicRes.xml`，文档根指定）对所有页可见；文档/页资源（`DocumentRes.xml`/`PageRes.xml`）作用域更小，就近覆盖。
  - When to use: 解析图元引用时，按 页资源 → 文档资源 → 公共资源 顺序向上查找。
- **BaseLoc 约定资源根**：资源文件 `BaseLoc` 定义通用数据存储路径，如 `Res` 表示该资源文件引用的数据文件默认存于当前路径的 `Res` 目录下。
  - How: 解析资源内 `MediaFile` 等路径时，相对 BaseLoc 解析。

## Key Concepts
- **大纲树**：根 `Outlines` → `OutlineElem`（Title/Count/Expanded/Actions/Action/子 OutlineElem）。
- **CT_OutlineElem**：`Title`(必选)、`Count`(子叶子数参考值,默认0)、`Expanded`(默认true)、`Actions`/`Action`(激活时执行)、`OutlineElem`(子节点递归)。
- **资源文件结构（图20）**：`BaseLoc` + `ColorSpaces` / `DrawParams` / `Fonts` / `MultiMedias` / `CompositeGraphicUnits`。
- **资源类型**：字型、颜色空间、绘制参数、矢量图像、多媒体（位图/视频/音频）。
- **CT_MultiMedia**：`Type`(必选, 位图/视频/音频)、`Format`(BMP/JPEG/PNG/TIFF/AVS 等，TIF 不支持多页)、`MediaFile`(ST_Loc 必选)。

## Mental Models
- 资源作用域像**词法作用域**：内层（页）覆盖外层（公共）。
- Think of `BaseLoc` as the **working directory** for that resource file's relative paths.

## Anti-patterns
- **查找顺序错**：应从小作用域往大作用域找，先页后文档后公共；反向会命中错误资源。
- **忽视 BaseLoc**：资源内相对路径需基于其 `BaseLoc` 解析，不能直接相对包根。
- **TIF 多页假设**：多媒体格式明确 TIF 不支持多页。

## Reference Tables

表18 资源文件属性（节选）

| 名称 | 类型 | 说明 |
|---|---|---|
| BaseLoc | ST_Loc | 资源文件通用数据存储路径，必选 |
| ColorSpaces | CT_ColorSpace+ | 颜色空间集合，元素扩展 ID(ST_ID) |
| DrawParams | CT_DrawParam+ | 绘制参数集合 |
| Fonts | CT_Font+ | 字型集合 |
| MultiMedias | CT_MultiMedia+ | 多媒体集合 |
| CompositeGraphicUnits | CT_VectorG+ | 矢量图像（被复合图元引用） |

表19 多媒体属性

| 名称 | 说明 |
|---|---|
| Type | 多媒体类型：位图图像/视频/音频，必选 |
| Format | BMP/JPEG/PNG/TIFF/AVS 等，TIF 不支持多页，可选 |
| MediaFile | 指向包内多媒体文件位置，必选 |

## Key Takeaways
1. 资源两级作用域：公共（文档根）/ 文档 / 页，查找由内到外。
2. 资源实际文件在容器目录，索引在 `Res` XML；`BaseLoc` 决定相对根。
3. 五大资源类型：字型、颜色空间、绘制参数、矢量图像、多媒体。
4. 大纲是递归树，激活节点可触发动作序列。

## Connects To
- **ch04**: 资源在文档根 `CommonData` 指定；大纲在 `Outlines`
- **ch07**: 颜色空间/绘制参数在此定义，页面描述引用
- **ch08-ch10**: 图元引用资源中的字型/绘制参数/图像
