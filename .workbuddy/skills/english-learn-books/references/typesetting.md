# PDF 版式规范与 build_books.py 定制点

排版全部由 `scripts/build_books.py` 完成：Markdown → HTML（`markdown` 库）→ 无头 Chrome 打印 PDF → PyMuPDF 回填目录页码并写书签。改版式就改这个脚本，不要手工调 PDF。

---

## 一、依据与实测参数

### GB/T 18358-2009《中小学教科书幅面尺寸及版面通用要求》

标准原文要点（4.2 节）：

- **幅面尺寸**：义务教育（1–9 年级）教科书应采用 GB/T 788-1999 表 1 中的 **A5 或 B5**。
- **版心**：须符合表 1 规定；以图为主的教科书版心可大于表 1，但**订口、切口、天头、地脚宽度不得小于 7mm**。
- **正文字号分四类**：a 类 21P–16P（1–3 年级）、b 类 14P（3–4 年级）、**c 类 12P（5–9 年级及高中）**、d 类 10.5P（高中理科）。
- **目录、注释、练习等用字**可适当减小，但**义务教育小学阶段最小用字不得小于 10.5P（5 号）**，初中与高中不得小于 9P。
- **行数与字数**：外语等学科教科书版心规格应符合表 1，但**不受每面行数、每行字数限制**。

### 本项目实测参数（`build_books.py` L73–128）

| 项目 | 取值 | 与国标的关系 |
|---|---|---|
| 成品尺寸 | **175mm × 260mm** | **非标开本**。国标标准幅面为 A5(148×210)、B5(169×239)、A4(210×297)；附录 A 非标系列 1/16 开本为 184×260。本项目尺寸介于 B5 与 1/16 之间 |
| 订口 | 13mm | 符合（≥7mm） |
| 切口 | 10mm | 符合（≥7mm） |
| 天头 | 15mm | 符合（≥7mm） |
| 地脚 | 17mm | 符合（≥7mm） |
| 版心 | 152mm × 228mm | 由成品减去四边得出，不落在国标表 1 任一档 |
| 正文字号 | **10.5pt** | **正好是国标对小学教科书的最小用字下限**（d 类字号）。⚠️ 不可再调小 |
| 正文行高 | 1.75 | 外语学科不受行数限制，取宽行距便于阅读 |
| 页码 | 9pt、`#1a4f82`、页脚居中 | 低于 10.5pt 下限，属页码非正文用字，惯例允许 |

**改字号时的硬约束**：小学阶段正文与表内文字不得低于 10.5pt。当前表体是 10pt（L331），严格说已低于小学下限——这是既定取舍（表格信息密度优先），若日后要完全合规需把表体提到 10.5pt 并重新核算列宽预算。

### 其他版式依据

- **三线表**（L323 注释）：顶线、栏目线、底线，无竖线、无行间横线。依据课本惯例与 CY/T 170。
- **PEP 版式参照**：人教版 PEP 语文与英语教科书的版式风格（章标题色带、节标题左侧竖线、三线表、首行缩进两字）作为观感基准。**注意 PEP 只是版式参照，内容与词表一律以教科版（广州版）为准**——广州小学不用 PEP 教材。

---

## 二、字体与字号体系

| 元素 | 字号 | 颜色 | 字体族 | 位置（行号） |
|---|---|---|---|---|
| 正文 | 10.5pt / 行高 1.75 | `#1c1916` | Songti SC → STSong → Times New Roman | L132–139 |
| 段落 | 首行缩进 2em，两端对齐 | — | `text-justify: inter-ideograph`、`line-break: strict` | L147–153 |
| 封面 h1 | 26pt，字距 0.12em | `#1a4f82` | 黑体族 | L170–179 |
| 部分 h1 | 22pt，字距 0.2em，`::after` 22mm 横线 | `#1a4f82` | 黑体族 | L202–217 |
| 章 h2 | **16pt**，白字 + 蓝底 `#1f6fb2` 色带 | `#fff` | 黑体族 | L219–226 |
| 节 h3 | **12pt**，左边框 3.2pt `#1f6fb2` | **`#1a4f82`** | 黑体族 | L227–234 |
| 习题 p.exercise | **12pt**（与 h3 相同），左边框 3.2pt `#e07b2a` | **`#c45c12` 橙** | 黑体族 | L235–249 |
| 表题 p.tablecap | 10.5pt，居中，无缩进 | `#1a4f82` | 同正文 | L311–321 |
| 表体 | 10pt / 行高 1.45 | — | 同正文 | L331–332 |
| 目录内 h3 | 11pt，去左边框 | `#1a4f82` | — | L260–269 |
| 音标 span.ipa | 继承 | `#4e5964`，nowrap | Times New Roman | L360 |

**⚠️ 关键约束：h3 与 p.exercise 字号完全相同（都是 12pt，边距行高也刻意对齐）**，唯一区别是颜色。书签采集靠 `ORANGE = 0xC45C12` 排除习题段。若日后改动这两者的字号或颜色，必须同步改 `collect_headings()`，否则「习题」会混进书签和目录页码表。

---

## 三、表格列宽自适应（本项目最大的定制点）

`table-layout: auto` 按**最小内容宽度**分配列宽，中文列的最小宽度近乎为零，会导致「I / me」这种窄列和「形容词性物主代词」这种宽列均分宽度，长文折行而短文留白。因此脚本改为 `fixed` + 显式 `<colgroup>` 列宽。

三段式算法：

1. **`measure_text()`（L738–763）** 按 em 估算宽度。权重：CJK 全角 = 1.0、IPA 音标区 = 0.55、窄字符 `ijlI.,;:!|'` 与空格 = 0.28、`mwMW` = 0.85、其他大写 = 0.68、其余拉丁 = 0.52、NBSP = 0.3。原则是**宁可略微高估，也不要低估**。
2. **`longest_tokens()`（L774–809）** 求单元格内真正不可断片段的宽度。`span.ipa` 整条视为原子（CSS nowrap）；英文词与数字不可断；**中文任意字间可断，只保留 2.0em 余量**（避免行尾出现孤立单字）。
   - 历史 bug：曾把整段中文当不可断片段（算出 16em），导致真正有富余的窄列被「饿死」。
3. **`set_column_widths()`（L812–901）** 分配。预算 `avail_em = 43.0`（版心宽换算的 em 数）。
   - 每列 `floor` = 最长不可断片段 + padding 1.2em（单列下限封顶 10em）；`demand` = 最长单元格全文宽（软上限 16em）。
   - **正常分支**（L880–888）：先付 floor，剩余宽度按各列 `extra_need` 比例分配。
   - **溢出分支**（L860–879）：总 floor 超预算时，短列（≤10em，不可断 token 密集）保完整，只压缩被封顶的长列（CJK 可中途断）；若短列本身也溢出，退化为整体等比缩放。
   - 输出注入 `<colgroup><col style="width:N%">` 并给 table 补 `table-layout:fixed`。

**⚠️ 封面表必须单独传预算**：`.cover table` 宽 88%，列宽预算要传 `43.0 * 0.88`（L946–947），否则窄列被挤折行。

其他表格规则：

- `thead { display: table-header-group }` 表头跨页重复；`tr { break-inside: avoid }` 行不拆断。
- `mark_wide_tables()`（L446–455）：首行 ≥6 列加 `class="wide"`，行高降 1.35、padding 减至 2.6pt 3.2pt。
- `mark_vocab_tables()`（L458–475）：表头前四列恰为 `词条/音标/释义/说明` 时加 `class="vocab"`，首列 Arial 700、`#1a4f82`、nowrap。可与 wide 叠加。
- `protect_cell_text()`（L478–491）：`★○◆●` 标记后用 NBSP 黏住词形；`/xxx/` 音标包 `span.ipa` 防拆行。
- **表号 `表 N-M` 是 md 里手写的，脚本只识别不重编号**；图号则相反，由 `decorate()`（L505–523）按当前章号自动生成 `N-M` 前缀。

---

## 四、目录（TOC）与三级书签

### 目录来源

目录就是 md 里的一节 `## 目录`，内容是手写的 Markdown 链接列表。`build_html()`（L962–964）识别章标题为「目录」时，对该节调用 `toc_links()` 并挂 `class="chapter toc"`。

**目录必须写成三级**（部分 → 章 → 缩进小节），且不收录卷首：

```markdown
## 目录

### [第一部分 自然拼读](#第一部分-自然拼读)

- [第一章 字母的名字和字母的音](#第一章-字母的名字和字母的音)
  - [1.1 二十六个字母的常见读音](#11-二十六个字母的常见读音)
```

`toc_links()`（L535–547）把每个链接改写为 flex 三件套：`toc-name` + `toc-leader`（点线引导）+ `toc-page data-toc="键">000`。键 = 条目纯文本归一化后 HTML 转义。

### 页码回填需要两到三次渲染

1. 渲染草稿 `full-pass1.pdf` → `heading_pages()` 取真实页码 → `fill_toc()` 回填 → 重写 HTML → 渲染正式 PDF。页码只有排版后才可知，所以必须两遍。
2. **漂移校验**（L1059–1072）：`toc_numbers()` 从成品 PDF 解析目录印出的页码，与实测比对；若填入页码后回流改变了分页（`shown != page`），重新 fill_toc 并**第三次渲染**，打印 `TOC shifted, reprinted`。
3. 无目录的书（HTML 里没有 `data-toc="`）只渲染一次。

### 目录 CSS

`section.toc { column-count: 2; column-gap: 8mm; column-rule: 0.5pt solid #dfe8f0 }`；目录内 h2/h3 `break-after: avoid`，每个 `ul` 整体不跨栏；引导线 0.6pt dotted `#8eb4d4`；页码固定 2.2em 右对齐、`font-variant-numeric: tabular-nums` 等宽数字。

### 书签采集 `collect_headings()`（L550–626）

目录页码回填与书签**共用同一个采集器**，四条过滤规则：

1. **字号阈值 `size < 10.8` 丢弃**：部分 h1≈22pt、章 h2=16pt、节 h3=12pt 都过关，正文 10.5pt 与表题 10.5pt 被排除。
2. **颜色排除 `ORANGE = 0xC45C12`**：任一行含该色 span 即跳过——剔除与 h3 同字号的「习题」段。
3. **跳过封面（`index == 0`）**：封面上 12pt 的副标题会被误判为标题。
4. **跳过目录页区间**：全扫描找文本恰为「目录」的行所在页定 `toc_start`；从 `toc_start+1` 起找第一个含 `size >= 20` 行（部分 h1）的页为 `toc_end`；找不到则 `toc_end = toc_start + 1`。区间内的页全部跳过，因为印刷目录的每一条都重复了所有标题。

折行合并：按 y 排序后，垂直距离 <30 且字号差 <2 的相邻线拼为一条标题。

### 书签层级 `add_outline()`（L988–1021）

**按标题模式优先、字号兜底**：

- 先探测全书是否有「第X部分」标题 → `has_part`
- `^第[一二三四五六七八九十]+部分` → level 1
- `^第…章` → `2 if has_part else 1`
- 否则 `size >= 14.5`（区分 16pt h2 与 12pt h3 的中间值）→ 2/1
- 其余 → 3/2

即**无部分层的书整体升一级**（自然拼读、学生本只有两级）。

两条附加规则：

- 跳过标题恰为「习题」的条目——`decorate()` 只把段落形式的「习题」转成橙色 p.exercise，写成 `### 习题` 的（如初中册）不会变色，只能按名排除。
- **`level = min(level, last + 1)`**：PDF 书签层级只允许逐级加深，跳级会让 `set_toc()` 抛 `bad hierarchy level`。

最后 `doc.set_toc(toc, collapse=0)` + `doc.set_pagemode("UseOutlines")`（打开 PDF 默认展开书签面板），存 `*.outline.pdf` 临时文件后 `tmp.replace()` 原子替换。

**⚠️ PDF 被 IDE 预览占用时 `replace` 会 PermissionError**，等锁释放后重试，不要杀 chrome 进程。

---

## 五、标题锚点 `add_heading_ids()`（L685–721）

目录用 GitHub 风格锚点（`#第一章-人体部位`），但无头 Chrome 打印时标题不带 `id`，导致**目录条目全部指向空、成品 PDF 无可点击链接**。脚本给 h1–h4 补 slug：

- 去 HTML 标签 → `strip().lower()` → 删 `` ` `` `*` `_` `~` `[` `]` `(` `)` → 保留 `\w`、`\u4e00-\u9fff`（中文）、空白、连字符，其余全删 → 空格换 `-` → 连续 `-` 折叠 → 去首尾 `-`
- 重复 slug 追加 `-1`、`-2`…（对齐 GitHub 行为）
- 已带 `id=` 的原样跳过；空 slug 兜底 `"section"`

**改标题文字后必须同步改目录里的锚点**，否则链接失效（`check_books.py` 会报「目录链接无对应标题」）。目录一律用脚本重建，不要手改。

---

## 六、中英文混排 `tighten_latin()`（L724–735）

对每个 `<h1>`（封面书名与部分标题）内部的拉丁单词包 `<span class="latin">`，配 `.latin { letter-spacing: 0 }`（L180）。

原因：h1 级标题有大字距（封面 0.12em、部分 0.2em、`.cover .meta` 0.32em），`letter-spacing` 逐字符施加会把 KET、PET 拆成「K E T」。归零拉丁词字距后，英文缩写保持紧凑，中文仍享受疏朗字距。

正文侧靠 `text-justify: inter-ideograph` + `line-break: strict` 实现中西文混排的标点禁则与避头尾；`em/i` 切 Times New Roman。

---

## 七、渲染链路与构建命令

```
md → markdown.markdown(extensions=["tables", "sane_lists"])
   → decorate()            图编号/figure 化、「习题」段转 p.exercise、表题转 p.tablecap、图片 src 换 file:// URI
   → mark_wide_tables() → mark_vocab_tables() → protect_cell_text()
   → 按 h1/h2 切块，分派为 cover / part / chapter
   → set_column_widths()（封面传 43.0*0.88）
   → 「目录」节走 toc_links()
   → add_heading_ids() → tighten_latin()
   → 写临时 HTML 到 %TEMP%\english-learn-pdf\
   → Chrome --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf
   → fill_toc（两到三次渲染）
   → add_outline()
```

依赖：`markdown`、`PyMuPDF`（函数内延迟 `import fitz`）、系统 Chrome 或 Edge（`find_chrome()` L19–43 在 Windows 试 5 个候选路径）。**无 requirements.txt**，环境里已装好。Python 解释器用 `C:\Users\gaoshiqiang\.workbuddy\binaries\python\envs\default\Scripts\python.exe`。

构建命令：

```bash
cd D:/workspace/opensource/english-learn
python scripts/build_books.py                       # 五本全部重建
```

单本重建（改一本书时更快）：

```python
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('bb', 'scripts/build_books.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
bb.write_book(Path('小学英语辅导手册.md').resolve(), '小学英语辅导手册',
              'full-book.html', Path('小学英语辅导手册.pdf').resolve())
```

验证产物（页数、书签层级分布、内部链接数）：

```python
import pymupdf
d = pymupdf.open('小学英语辅导手册.pdf')
lv = {}
for t in d.get_toc():
    lv[t[0]] = lv.get(t[0], 0) + 1
print(d.page_count, len(d.get_toc()), lv, sum(len(p.get_links()) for p in d))
```

`main()`（L1077–1107）五本书配置：

| md | 封面标题 | 临时 HTML |
|---|---|---|
| 小学英语辅导手册-学生本.md | 小学英语辅导手册 · 学生本 | slim-book.html |
| 小学英语辅导手册.md | 小学英语辅导手册 | full-book.html |
| 初中英语学习辅导手册.md | 初中英语学习辅导手册 | junior-book.html |
| 自然拼读.md | 自然拼读 | phonics-book.html |
| 小学英语-KET-PET辅导手册.md | 小学英语 · KET · PET 辅导手册 | ket-pet-book.html |

临时 HTML 名沿用历史命名（slim/full/junior/phonics/ket-pet），与书名无关，改名时不必动。

---

## 八、写 md 时的排版约定

- 表格前必须空一行，否则 Markdown 不解析为表格。
- 表题写成 `表 N-M　标题`（**N-M 后是全角空格 U+3000**），独占一行、无句末标点、全长 ≤36 字，脚本才会识别为 `p.tablecap` 并居中。校验脚本也按全角空格识别表题。
- 「习题」写成独占一行的段落文字（脚本转橙色 p.exercise），**不要写成 `### 习题`**——写成 h3 会进书签，只能靠按名排除。
- 图片放 `images/`，md 里用相对路径 `images/xxx.png`，图号由脚本按章自动生成，不要手写。
- 章节重排后目录必须重建，锚点要跟着标题文字变。
