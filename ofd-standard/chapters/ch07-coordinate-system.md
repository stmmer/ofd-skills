# Chapter 7: 页面描述（§8）

## Core Idea
OFD 用三类坐标空间描述图元：**设备空间**（输出相关）、**页面空间**（与设备无关，原点左上、X 右、Y 下、毫米）、**对象空间**（图元内部，以其外接矩形左上角为原点）。空间间用平移/缩放/旋转/切变（变换矩阵 CTM）转换。颜色、绘制参数、裁剪区、底纹与渐变都在这一层定义。

## Frameworks Introduced
- **三类坐标空间分工**：
  - 设备空间：设备自身坐标，内容不应直接在此描述。
  - 页面空间：与设备无关，左上角原点，X 右增、Y 下增，单位毫米；整页大小由 `PageArea/PhysicalBox` 决定。
  - 对象空间：图元内部坐标，以其外接矩形左上角为原点，X 右、Y 下、毫米。
  - When to use: 图元先经外接矩形平移进对象空间，再按 CTM 与裁剪绘制。
- **变换矩阵 CTM**：空间间变换用矩阵表示（平移/缩放/旋转/切变），对象空间的变换矩阵字段见各图元（`CTM`，`ST_Array`）。

## Key Concepts
- **绘制参数 DrawParam**：结构含线宽、颜色、线连接样式、端点样式、虚线样式等；可在资源中定义后引用。
- **颜色空间 ColorSpace**：`DefaultCS` 不存在时默认 RGB；支持基础颜色、底纹（Patterm）、渐变。
- **底纹 Patterm（§8.3.3）**：以 `CellContent`(CT_PageBlock) 为单元平铺填充；属性 Width/Height/XStep/YStep/RelativeTo(Page|Object)/ReflectMethod(Normal|Column|Row|RowAndColumn)/CTM。
- **渐变（§8.3.4）**：轴向（AxialShd）、径向（RadialShd）、高洛德（Gouraud）、网格高洛德；区间由起始点到结束点的一次颜色过渡；推荐配合裁剪区使用。
- **裁剪区 Clip**：限制图元绘制范围。
- **图元对象**：页面块内的可绘制单元（路径/文字/图像/复合/视频）。

## Mental Models
- 页面空间是**画布坐标系**，对象空间是**每个图元自己的局部画布**。
- Think of `CTM` as the **viewport transform** from local to page coordinates.
- 底纹 = 用一个小 PageBlock 当"瓷砖"平铺；渐变 = 预定义颜色过渡渲染模式。

## Anti-patterns
- **直接在设备空间描述内容**：标准禁止，必须走页面/对象空间。
- **忽略单位**：坐标一律毫米，不要当像素处理（输出时再按分辨率换算）。
- **渐变不配合裁剪**：渐变区域可能超出预期，应配合 Clip。

## Reference Tables

页面空间约定

| 空间 | 原点 | 轴方向 | 单位 |
|---|---|---|---|
| 设备空间 | 设备相关 | 设备相关 | 设备相关 |
| 页面空间 | 页面左上角 | X 右增 / Y 下增 | 毫米 |
| 对象空间 | 图元外接矩形左上角 | X 右增 / Y 下增 | 毫米 |

底纹属性（表28 节选）

| 名称 | 说明 |
|---|---|
| Width/Height | 底纹单元宽/高，必选 |
| XStep/YStep | 单元间距，缺省=宽/高（小于单元尺寸时按默认） |
| RelativeTo | Page / Object，默认 Object |
| ReflectMethod | Normal/Column/Row/RowAndColumn |
| CellContent | 底纹单元（CT_PageBlock），必选 |
| CTM | 单元变换矩阵，默认单位阵 |

## Worked Example
对象空间绘制一个 100×50 的矩形（外接矩形定位，内部坐标从 0,0 起）：
```xml
<ofd:PathObject Boundary="10 10 100 50" CTM="1 0 0 1 0 0">
  <ofd:FillColor .../>
  <ofd:FigureSegment> ... </ofd:FigureSegment>
</ofd:PathObject>
```

## Key Takeaways
1. 三类坐标空间：设备（输出）、页面（毫米、左上原点）、对象（图元局部）。
2. 坐标单位统一为毫米，像素换算推迟到输出阶段。
3. 颜色默认 RGB；底纹平铺、渐变过渡都在绘制参数/颜色层定义。
4. CTM 负责空间变换，裁剪区负责范围限制。
5. 绘制参数是资源，可复用。

## Connects To
- **ch04**: `DefaultCS` 在 CommonData 指定
- **ch06**: 颜色空间/绘制参数/字型是资源类型
- **ch08-ch10**: 图形/图像/文字都使用本层坐标与绘制参数
