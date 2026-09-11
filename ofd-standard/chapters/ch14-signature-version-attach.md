# Chapter 14: 数字签名、版本与附件（§18–20）

## Core Idea
OFD 内置三类"文档级附加能力"：**数字签名**（防篡改/身份认证，集中在 `Signs/`）、**版本**（记录因注释/改动产生的版本，见第19章）、**附件**（独立文件打包，见第20章）。签名与版本通过文档根 `Signatures`/`Versions` 引用，附件通过根 `Attachments` 引用。

## Frameworks Introduced
- **签名列表 + 签名文件（§18）**：`Signatures.xml` 列签名；每个 `Sign_N` 含 `Signature.xml`（签章描述）、`Seal.esl`（电子印章）、`SignedValue.dat`（签名值）。
  - When to use: 验真时按 `Signature.xml` 计算文件摘要并与 `SignedValue.dat` 比对；签章外观由 `Signature.xml` 描述。
- **版本 Versions（§19）**：文档根 `Versions` 含多个版本描述，记录注释/改动产生的版本信息。
- **附件 Attachments（§20）**：`Attachments.xml` 列表 + 各 `Attachment` 节点，打包任意外部文件。

## Key Concepts
- **签名范围（§18.2.2）**：签名文件声明被签名的对象范围；签名值（§18.2.4）覆盖该范围。
- **文件摘要（§18.2.1）**：对签名范围内文件计算摘要。
- **签名外观（§18.2.3）**：签章在页面上的可视化位置与样式。
- **版本入口（§19.1）/版本（§19.2）**：版本描述节点。
- **附件列表（§20.1）/附件（§20.2）**：附件元数据与引用。
- **文档根引用**：`Signatures`(ST_Loc)、`Versions`、`Attachments`(ST_Loc)。

## Mental Models
- 签名像 **清单 + 印章 + 指纹** 三部分：列什么被签、印章长啥样、值是多少。
- Think of `Signs/` as a **detached signature container** kept separate from content.

## Anti-patterns
- **改内容后不重算摘要**：会破坏签名有效性，必须按签名范围重新摘要。
- **忽略模板/资源也参与签名范围**：签名范围可能跨多个文件，需按声明覆盖。

## Reference Tables

签名目录结构（节选）

| 文件 | 作用 |
|---|---|
| Signs/Signatures.xml | 签名列表 |
| Signs/Sign_N/Signature.xml | 第 N 个签名描述（范围/外观/值引用） |
| Signs/Sign_N/Seal.esl | 电子印章文件 |
| Signs/Sign_N/SignedValue.dat | 签名值 |

## Key Takeaways
1. 签名三件套：列表 + 签章描述 + 印章 + 签名值，集中在 `Signs/`。
2. 验真按签名范围计算摘要并比对 SignedValue。
3. 版本记录注释/改动产生的时间线。
4. 附件是独立打包文件，列表在 `Attachments.xml`。
5. 三者都通过文档根 ST_Loc 引用。

## Connects To
- **ch03**: 容器层次中的 Signs/ 目录
- **ch04**: 文档根 Signatures/Versions/Attachments 节点
