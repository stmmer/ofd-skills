# Chapter 3: 文件结构（§6）

## Core Idea
OFD 是 **ZIP 容器（ZIP 6.2.0 规范）** 内的多文件 XML 文档集合；整个包有且仅有一个固定文件名 `OFD.xml` 作为主入口，文件名不可修改。读取 OFD 的第一步永远是解包 ZIP 并定位 `OFD.xml`。

## Frameworks Introduced
- **容器即 ZIP**：一个 OFD 文件 = 一个符合 ZIP 6.2.0 的压缩包，内部按目录层次组织多个 XML 与资源文件。
  - When to use: 任何解析/生成 OFD 的代码，第一步都是 ZIP 解包，不是直接读字节。
- **主入口唯一且固定**：包根目录下必须存在且只能存在一个 `OFD.xml`，名字不可改。
  - How: 解析器以 `OFD.xml` 为根，按其中 `DocBody/DocRoot` 指向逐层加载。

## Key Concepts
- **OFD.xml**：文档主入口文件，声明版本、类型、文档体、元数据、根节点位置、签名、版本信息。
- **Doc_N / Document.xml**：第 N 个文档文件夹及其根节点描述文件（一个 OFD 包可含多个版式文档）。
- **Pages / Page_N / Content.xml**：第 N 页文件夹与页面内容描述。
- **Res / PublicRes.xml / DocumentRes.xml**：资源目录与公共资源、文档资源索引文件。
- **Signs / Signatures.xml / Seal.esl / SignedValue.dat**：数字签名存储目录与签名相关文件。
- **扩展名**：标准规定文件扩展名为 `.ofd`。

## Mental Models
- 把 OFD 文件想成**一个小型文件系统**：ZIP 是磁盘，`OFD.xml` 是 `C:\` 下的 boot 记录，其余 XML 是各分区。
- Think of `OFD.xml` as the **table of contents** that every other file hangs off of.

## Anti-patterns
- **直接按字节解析 OFD**：OFD 不是流式二进制格式，必须先 ZIP 解包再解析 XML。
- **假设文件名可变**：`OFD.xml` 名称固定，不要做大小写/扩展名猜测；大小写敏感（路径约定见基础类型）。
- **忽略多文档**：一个包内可含多个 `Doc_N`，不要硬编码单文档假设。

## Reference Tables

表1 OFD 文件层次组织结构（关键项）

| 名称 | 说明 |
|---|---|
| `OFD.xml` | 文档主入口，包内唯一，文件名不可改 |
| `Doc_N/` | 第 N 个文档的文件夹 |
| `Document.xml` | 文档的根节点 |
| `Pages/` | 页文件夹 |
| `Page_N/Content.xml` | 第 N 页的内容描述 |
| `Page_N/Res/PageRes.xml` | 第 N 页的资源描述 |
| `Res/` | 资源文件夹 |
| `PublicRes.xml` | 文档公共资源索引 |
| `DocumentRes.xml` | 文档自身资源索引 |
| `Image_M.png` / `Font_M.ttf` | 资源文件（图像/字型等） |
| `Signs/Signatures.xml` | 签名列表文件 |
| `Signs/Sign_N/Signature.xml` | 第 N 个签名描述文件 |
| `Signs/Sign_N/Seal.esl` | 电子印章文件 |
| `Signs/Sign_N/SignedValue.dat` | 签名值文件 |

## Worked Example
最小可解析的 OFD 包骨架：
```
archive.ofd  (ZIP 6.2.0)
├─ OFD.xml
├─ Doc_0/
│  ├─ Document.xml
│  └─ Pages/
│     └─ Page_0/
│        ├─ Content.xml
│        └─ Res/PageRes.xml
└─ Res/PublicRes.xml
```

## Key Takeaways
1. OFD = ZIP 6.2.0 容器，不是单文件二进制格式。
2. `OFD.xml` 是唯一且文件名固定的主入口。
3. 资源按作用域分公共资源（`PublicRes.xml`）与文档/页资源（`DocumentRes.xml` / `PageRes.xml`）。
4. 一个包可包含多个 `Doc_N` 文档体。
5. 数字签名集中在 `Signs/` 目录，与主内容分离。

## Connects To
- **ch04**: `OFD.xml` 的内部结构由 §7.4 主入口定义
- **ch06**: 资源文件结构见 §7.9
- **ch15**: 各 XML 的 Schema 见附录 A
