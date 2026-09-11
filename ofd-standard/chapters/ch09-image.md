# Chapter 9: 图像（§10）

## Core Idea
图像由**图像对象 ImageObject（CT_Image）** 描述，引用资源中已定义的图像资源（PNG/JPEG/TIFF/BMP 等），通过外接矩形 `Boundary` 与变换矩阵 `CTM` 定位到页面空间，可裁剪、缩放、做不透明度与遮罩处理。

## Frameworks Introduced
- **图像 = 资源引用 + 定位**：`ImageObject` 不内嵌像素，而是通过资源 ID 引用 `Res` 中定义的图像资源。
  - When to use: 渲染前先从资源（页/文档/公共）按 ID 取图像字节，再按 Boundary/CTM 绘制。

## Key Concepts
- **CT_Image（ImageObject）**：含 `Boundary`(ST_Box)、`CTM`、`ResourceID`(ST_RefID 引用资源图像)、`Clip`(可选裁剪)、透明度等。
- **图像资源**：定义在资源文件 `MultiMedias` 或专门图像资源节点，格式见 §7.9 多媒体（`Format` 支持 BMP/JPEG/PNG/TIFF/AVS，TIF 不支持多页）。
- **子像素/插值**：标准对图像缩放的插值方式可规定。
- **遮罩与透明度**：支持按图元参数控制图像呈现。

## Mental Models
- 图像对象像 **HTML 的 `<img>`**：src 指向资源，style 决定位置/大小/裁剪。
- Think of `Boundary` as the **dest rect**, `CTM` as the transform applied before painting.

## Anti-patterns
- **内嵌像素假设**：图像字节在资源文件，不在 Content.xml 内。
- **忽略资源作用域**：图像资源可能定义在页/文档/公共三级，按作用域查找。
- **TIF 多页假设**：TIF 格式不支持多页，取首页。

## Reference Tables

图像对象关键属性

| 名称 | 类型 | 说明 |
|---|---|---|
| Boundary | ST_Box | 图像外接矩形（目标位置/大小） |
| CTM | ST_Array | 变换矩阵 |
| ResourceID | ST_RefID | 引用资源中的图像，必选 |
| Clip | — | 裁剪区，可选 |

## Worked Example
```xml
<ofd:ImageObject Boundary="20 20 200 150" ResourceID="200">
  <ofd:Clip> ... </ofd:Clip>
</ofd:ImageObject>
```

## Key Takeaways
1. 图像是资源引用 + 定位（Boundary/CTM），不内嵌像素。
2. 图像资源按作用域从资源文件查找。
3. 支持裁剪、缩放、透明度。
4. TIF 资源不支持多页。

## Connects To
- **ch06**: 图像资源定义在 Res 文件（多媒体/图像资源）
- **ch07**: 在页面/对象空间用 CTM 绘制
- **ch05**: ImageObject 是 PageBlock 子图元
