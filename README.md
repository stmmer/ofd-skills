# ofd-skills

两个配套的 Agent Skill，覆盖 **GB/T 33190—2016 电子文件存储与交换格式（版式文档 / OFD）**
从"规范怎么说的"到"文件怎么读出来"的完整链路。

| Skill | 角色 | 内容 |
|---|---|---|
| [`ofd-standard`](ofd-standard/) | **契约基准** | 标准知识库：15 章结构化笔记、术语表、速查表、附录 A 的 13 个 XSD、离线结构校验器 |
| [`ofd-reader`](ofd-reader/) | **执行器** | 纯标准库 OFD 解析器：文本 / 图像 / 大纲 / 模板页 / 复合对象 / 注释 / 动作 / 数字签名抽取 |

> 需要核对某个元素的规范定义 → 查 `ofd-standard`。
> 需要真的把一个 `.ofd` 文件读出来 → 用 `ofd-reader`。

## 安装

把对应目录复制到 Agent 的 skills 目录即可（两个都装才能用上 `--validate` 的强 Schema 校验）：

```bash
# WorkBuddy
cp -r ofd-standard ofd-reader ~/.workbuddy/skills/

# Claude Code / Codex 等（技能目录按各自约定）
```

## 用法

```bash
PY="python"    # 3.8+，无需 pip 安装任何依赖
SK="~/.workbuddy/skills/ofd-reader/scripts"

# 文本 + 图像 + 结构化 Markdown
"$PY" "$SK/cli.py" "文档.ofd" --md out.md --images --out images

# 元信息 / 大纲 / 签名 / 注释 / 动作
"$PY" "$SK/cli.py" "文档.ofd" --info

# 结构校验（宽松）；装了 lxml 且 ofd-standard 在场时追加附录 A 强校验
"$PY" "$SK/cli.py" "文档.ofd" --validate

# 自带合成样例自检（21 项断言）
"$PY" "$SK/selftest.py"
```

Python API 见 [`ofd-reader/SKILL.md`](ofd-reader/SKILL.md)。

## 目录结构

```
ofd-skills/
├── ofd-standard/          # 契约基准（知识库）
│   ├── SKILL.md
│   ├── chapters/          # ch01–ch15 标准笔记
│   ├── schemas/           # 附录 A 的 13 个 XSD（标准原文）
│   ├── tools/             # extract_appendix_xsd.py — 从标准 PDF 复原 schemas/
│   ├── cheatsheet.md  glossary.md  patterns.md
│   └── validate.py        # 离线 XSD 校验器（需 lxml）
└── ofd-reader/            # 执行器（解析器）
    ├── SKILL.md
    ├── scripts/
    │   ├── cli.py
    │   ├── selftest.py
    │   └── ofdreader/     # container / parser / resources / extract / validate / ns / model
    └── references/pitfalls.md     # 10 条真实文件踩坑清单
```

## 设计要点

- **零依赖**：`ofd-reader` 仅用 Python 标准库（`zipfile` + `xml.etree.ElementTree`）。
- **对真实文件宽容**：WPS / 点聚 / 数科 普遍产出 OFD **v1.1**、数字型 `ST_ID`、厂商扩展节点，
  严格按附录 A 校验会误杀。解析必须宽松，Schema 校验只作告警。
- **模板页必展开**：红头 / 页眉 / 水印常在 `TemplatePage` 里，只读本页 `Content.xml` 会整层丢失。

## 许可与来源

- `ofd-reader/` — MIT，见 [LICENSE](LICENSE)。
- `ofd-standard/` — 内容为 GB/T 33190—2016 的学习性结构化笔记，
  以及从标准 PDF **附录 A 原文复原**的 XSD，**非官方发布物**，
  版权与许可见 [NOTICE.md](NOTICE.md)。要点：
  - 章节笔记为学习性整理，标准文本著作权归属发布机构；
  - `schemas/` 下 13 个 XSD 由 `ofd-standard/tools/extract_appendix_xsd.py`
    从标准 PDF 附录 A 确定性复原，13/13 可编译、且与社区转录版
    [GreenYun/OFD-Schema](https://github.com/GreenYun/OFD-Schema) 去空白后逐字符一致
    （两条独立路径互为印证），并保留了标准自带的 31 条中文注释；
    详见 [schemas/README.md](ofd-standard/schemas/README.md)。


## 验证状态

在真实文件《北京点聚红头文件.ofd》（WPS 生成，10 页，含数字签名）上端到端验证：

- 10 页文本抽取，阅读顺序正确（如 `2004年 8月 28日`）
- 红头图抽取（`page_01_img_43.png`）
- 数字签名：1 个 Seal（点聚 DJ 2.0），保护 19 个文件，签章在第 1 页
- `--validate` 宽松结构校验全 PASS
- 合成样例自检 21 项全 PASS（覆盖模板页 / 复合对象 / 注释 / 动作 / 签名）
