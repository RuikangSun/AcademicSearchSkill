# Academic Full Search Skill
| 字段 | 内容 |
|------|------|
| name | academic-full-search |
| description | 全量覆盖主流平台的学术搜索技能。**触发规则**：用户提及“学术调研、文献查找、主题综述、参考文献、引文溯源、预印本检索、GB/T 7714/APA/MLA引用格式生成”时自动触发，禁止被通用网页搜索替代。**覆盖数据源**：arXiv、bioRxiv、chemRxiv、medRxiv、chinaxiv全系列预印本、PubMed、Google Scholar、ResearchGate。**禁用边界**：非学术类内容禁止调用。 |
| version | 1.1.0 |
| last_update | 2026-03-26 |
| required_env | Python 3.9+基础环境、智能体内置Playwright+Chromium组件 |


## Prerequisites 前置检查
### 1. 环境确认
- 确认智能体已内置Playwright及Chromium无头组件（无需用户额外安装）；
- 确认Python 3.9+基础环境可用，无额外依赖包要求。

### 2. 配置读取
优先读取`config/search_config.yaml`中的配置项，无配置文件时，默认启用本手册中全部数据源、最大3轮检索、单平台请求间隔≥2秒的基础规则。


## Workflow 标准化执行工作流（含详细实现参数）
智能体必须严格按以下步骤执行，禁止跳步、随意缩减检索范围。

---

### Step 1：需求澄清（必填参数确认）
执行检索前，必须先向用户确认以下信息，未明确项使用默认值：
- 【必填】检索核心主题/关键词/研究问题；
- 【可选】时间范围（默认：近10年）；
- 【可选】文献类型（期刊论文/预印本/学位论文/专利，默认：全类型）；
- 【可选】排除数据源（默认：全数据源启用，无排除）；
- 【可选】输出文献数量（默认：20篇，上限50篇）；
- 【可选】参考文献格式（默认：GB/T 7714-2015 顺序编码制，可选APA/MLA）；
- 【可选】是否限制检索轮次（默认：最多3轮，含首轮）。

---

### Step 2：全量多源并行检索（核心逻辑+详细实现参数）
#### 2.1 检索核心原则
**取消数据源优先级，对所有启用的数据源执行全量并行检索**。
各数据源收录范围相互独立、仅部分重叠：预印本平台仅收录本平台发布的论文、PubMed仅限生命科学/医学领域、Google Scholar/ResearchGate收录范围最全但可能存在访问限制，仅全量并行检索可最大化覆盖相关文献，避免遗漏。

#### 2.2 第一阶段：全量公共API并行检索（无密钥、免登录，含详细参数）
对所有具备公开无密钥API的数据源，同时发起并行检索，记录每个数据源的检索状态、返回结果数量。

##### 2.2.1 arXiv公共API实现
- **API端点**：`http://export.arxiv.org/api/query`
- **核心请求参数**：
  | 参数 | 类型 | 必填 | 说明 | 示例 |
  |------|------|------|------|------|
  | `search_query` | str | 是 | 检索条件，支持字段前缀（`all:`全字段、`ti:`标题、`au:`作者、`abs:`摘要、`cat:`学科分类），布尔运算符`AND/OR/NOT`，空格用`+`编码 | `all:machine+learning+AND+cat:cs.CV` |
  | `start` | int | 否 | 分页偏移量，默认0 | `0` |
  | `max_results` | int | 否 | 单页最大结果数，默认10，上限1000 | `50` |
  | `sortBy` | str | 否 | 排序依据：`relevance`（相关性）、`submittedDate`（提交时间）、`lastUpdatedDate`（更新时间） | `submittedDate` |
  | `sortOrder` | str | 否 | 排序顺序：`ascending`（升序）、`descending`（降序） | `descending` |
- **时间范围过滤**：通过`search_query`中的`submittedDate`字段实现，格式为`[YYYYMMDDTTTT+TO+YYYYMMDDTTTT]`（TTTT为24小时制分钟，GMT时区） | `submittedDate:[201601010000+TO+202603260000]` |
- **示例完整请求**：
  ```
  http://export.arxiv.org/api/query?search_query=all:artificial+intelligence+AND+submittedDate:[202101010000+TO+202603260000]&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending
  ```
- **返回格式**：Atom XML，需解析`<entry>`标签获取标题、作者、摘要、DOI、全文链接等信息；
- **限流规则**：单请求间隔≥2秒，禁止高频请求。

##### 2.2.2 PubMed E-utilities公共API实现
- **核心流程**：先用`ESearch`检索获取PMID列表，再用`EFetch`批量获取文献详情。
- **ESearch API（检索PMID）**：
  - **端点**：`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
  - **核心参数**：
    | 参数 | 类型 | 必填 | 说明 | 示例 |
    |------|------|------|------|------|
    | `db` | str | 是 | 数据库名称，固定为`pubmed` | `pubmed` |
    | `term` | str | 是 | 检索词，支持布尔运算符`AND/OR/NOT`，字段前缀`[TI]`标题、`[AB]`摘要、`[DP]`日期 | `cancer+immunotherapy[TI/AB] AND 2021/01/01[DP]:2026/03/26[DP]` |
    | `retmax` | int | 否 | 最大返回PMID数，默认20，上限100000 | `50` |
    | `retstart` | int | 否 | 分页偏移量，默认0 | `0` |
    | `sort` | str | 否 | 排序依据：`relevance`（相关性）、`date`（日期） | `date` |
    | `rettype` | str | 否 | 返回类型，固定为`xml` | `xml` |
    | `email` | str | 是 | 必须提供有效邮箱（用于NCBI联系，无密钥要求） | `academic.search@example.com` |
    | `tool` | str | 否 | 工具名称，便于NCBI统计 | `AcademicSearchSkill` |
  - **示例请求**：
    ```
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cancer+immunotherapy[TI/AB]&retmax=20&sort=date&email=academic.search@example.com
    ```
  - **返回**：XML格式，解析`<IdList>`下的`<Id>`标签获取PMID列表。
- **EFetch API（获取文献详情）**：
  - **端点**：`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
  - **核心参数**：
    | 参数 | 类型 | 必填 | 说明 | 示例 |
    |------|------|------|------|------|
    | `db` | str | 是 | 固定为`pubmed` | `pubmed` |
    | `id` | str | 是 | 用逗号分隔的PMID列表 | `38000001,38000002` |
    | `rettype` | str | 是 | 返回类型：`abstract`（摘要）、`medline`（完整元数据） | `medline` |
    | `retmode` | str | 是 | 返回格式：`xml`、`text` | `xml` |
    | `email` | str | 是 | 同ESearch | `academic.search@example.com` |
  - **示例请求**：
    ```
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=38000001,38000002&rettype=medline&retmode=xml&email=academic.search@example.com
    ```
  - **返回**：XML格式，解析获取标题、作者、摘要、DOI、发表期刊、日期等信息；
  - **限流规则**：无API密钥时≤3 req/s，单EFetch请求PMID数≤10000。

##### 2.2.3 bioRxiv/medRxiv/chemRxiv公共API实现
- **统一API端点格式**：
  - 按日期范围检索：`https://api.medrxiv.org/details/[server]/[start_date]/[end_date]/[cursor]/[format]`
  - 按DOI单篇检索：`https://api.medrxiv.org/details/[server]/[DOI]/na/[format]`
- **核心参数**：
  | 参数 | 类型 | 必填 | 说明 | 示例 |
  |------|------|------|------|------|
  | `server` | str | 是 | 预印本平台：`biorxiv`、`medrxiv`、`chemrxiv` | `biorxiv` |
  | `start_date`/`end_date` | str | 是 | 日期范围，格式`YYYY-MM-DD`（仅日期范围检索时用） | `2021-01-01`/`2026-03-26` |
  | `cursor` | int | 否 | 分页游标，默认0，单页返回100条结果 | `0` |
  | `format` | str | 是 | 返回格式：`json`、`xml` | `json` |
  | `DOI` | str | 是 | 单篇检索时的文献DOI（仅DOI检索时用） | `10.1101/2024.01.01.573849` |
- **示例日期范围检索请求**：
  ```
  https://api.medrxiv.org/details/biorxiv/2021-01-01/2026-03-26/0/json
  ```
- **返回格式**：JSON/XML，解析获取标题、作者、摘要、DOI、发布日期、PDF链接等信息；
- **关键词过滤**：API不直接支持关键词检索，需先获取日期范围内的文献元数据，再由智能体在本地通过标题/摘要匹配关键词；
- **限流规则**：单请求间隔≥2秒。

##### 2.2.4 chinaxiv公共API实现
- **API端点**：`https://www.chinaxiv.org/api/search`
- **核心参数**：
  | 参数 | 类型 | 必填 | 说明 | 示例 |
  |------|------|------|------|------|
  | `keyword` | str | 是 | 检索关键词 | 人工智能 |
  | `startDate` | str | 否 | 开始日期，格式`YYYY-MM-DD` | 2021-01-01 |
  | `endDate` | str | 否 | 结束日期，格式`YYYY-MM-DD` | 2026-03-26 |
  | `page` | int | 否 | 页码，默认1 | 1 |
  | `pageSize` | int | 否 | 单页结果数，默认10，上限50 | 20 |
- **示例请求**：
  ```
  https://www.chinaxiv.org/api/search?keyword=人工智能&startDate=2021-01-01&endDate=2026-03-26&page=1&pageSize=20
  ```
- **返回格式**：JSON，解析获取标题、作者、摘要、DOI、发布日期、全文链接等信息；
- **限流规则**：单请求间隔≥2秒。

#### 2.3 第二阶段：内置Chromium全量兜底检索（含详细操作步骤）
对无公开无密钥API、API调用失败、访问受限的数据源，同步使用智能体内置Chromium无头模式执行检索，不得随意跳过任一启用的数据源。

##### 2.3.1 覆盖范围
Google Scholar、ResearchGate等无公开稳定API的平台。

##### 2.3.2 通用Chromium检索操作步骤（智能体自主执行）
1. **启动浏览器实例**：
   - 调用智能体内置Playwright的`chromium.launch()`，设置`headless=True`（无头模式）；
   - 配置浏览器上下文：设置随机User-Agent（如`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36`）、禁用WebRTC、设置视口大小（如1920x1080）；
   - 单请求间隔设置为2-5秒（随机，避免反爬）。

2. **Google Scholar详细检索步骤**：
   - **访问页面**：`page.goto("https://scholar.google.com/", wait_until="domcontentloaded")`；
   - **输入关键词**：定位搜索框（选择器`input[name="q"]`），输入用户确认的关键词，按`Enter`键或点击搜索按钮（选择器`button[type="submit"]`）；
   - **筛选条件**：
     - 时间范围：点击“Since 2016”或自定义范围（选择器`.gs_scl`下的时间选项）；
     - 文献类型：若需筛选综述，点击“Review articles”（选择器`.gs_nph`下的选项）；
   - **解析结果**：
     - 遍历结果条目（选择器`.gs_r.gs_or.gs_scl`）；
     - 提取标题：选择器`.gs_rt a`，获取文本和`href`属性（全文链接）；
     - 提取作者/期刊：选择器`.gs_a`，获取文本；
     - 提取摘要：选择器`.gs_rs`，获取文本；
     - 提取被引量：选择器`.gs_fl a:nth-child(3)`，获取文本中的数字；
     - 提取DOI：若全文链接包含DOI则提取，否则从元数据中推断；
   - **翻页操作**：若单页结果不足，点击“Next”按钮（选择器`.gs_nma:last-child`），最多翻3页；
   - **关闭页面**：完成后关闭当前标签页。

3. **ResearchGate详细检索步骤**：
   - **访问页面**：`page.goto("https://www.researchgate.net/", wait_until="domcontentloaded")`；
   - **输入关键词**：定位搜索框（选择器`input[placeholder*="Search"]`），输入关键词，按`Enter`键；
   - **筛选条件**：点击“Filters”按钮，选择时间范围、文献类型；
   - **解析结果**：
     - 遍历结果条目（选择器`.search-result-item`）；
     - 提取标题、作者、摘要、DOI、全文链接、发表时间；
   - **翻页操作**：点击下一页按钮，最多翻3页。

4. **关闭浏览器实例**：所有平台检索完成后，调用`browser.close()`关闭Chromium。

---

### Step 3：结果标准化处理（智能体自主完成，无额外代码依赖）
全量检索完成后，由智能体自主对所有数据源的结果进行统一处理，确保结果精准、无冗余：
1. **去重**：按「DOI号」为第一优先级、「标题+第一作者+发表年份」为第二优先级，剔除全量结果中的重复文献；
2. **合规筛选**：剔除无有效DOI/公开全文链接、撤稿、涉密、摘要缺失的无效文献；
3. **排序**：
   - 基础检索需求：按「关键词匹配度+发表时间倒序」综合排序；
   - 深度调研/综述需求：按「关键词匹配度+被引量（可获取时）+领域权威性」综合排序；
4. **数量控制**：按用户要求的数量截取Top N文献，有效文献不足时按实际数量输出，并向用户说明。

---

### Step 4：多轮深度补全检索（核心逻辑优化）
#### 4.1 触发规则（取消仅综述触发的限制，全需求适配）
首轮检索完成后，出现以下任一情况，智能体自动触发多轮补全检索，无需用户额外指令，最多执行3轮（含首轮）：
1. 从首轮结果中识别到与用户需求高度相关的**新核心关键词、细分研究方向**，未覆盖在用户原始检索词中；
2. 发现高被引、高相关的核心文献，其施引文献/参考文献存在重要补充价值；
3. 首轮检索结果数量不足、整体相关性偏低，需要优化关键词补充检索；
4. 用户明确要求全面检索、深度调研。

#### 4.2 补全检索执行逻辑
1. 从首轮结果中提炼补充关键词、细分研究方向，生成新的检索词组合；
2. 重复Step2的「全量多源并行检索」流程（含API和Chromium兜底），获取补全结果；
3. 对补全结果执行Step3的去重、筛选、排序流程，与首轮结果合并；
4. 多轮终止条件：无新的核心补充关键词、单轮补全有效文献<3篇、达到最大3轮限制。

---

### Step 5：标准输出与交付
#### 5.1 固定交付内容
直接向用户交付以下完整内容，无需依赖额外存储目录：
1. 标准化学术检索报告（Markdown格式，对话内直接展示，按下方模板生成）；
2. 可直接复制使用的BIB格式参考文献；
3. 检索执行说明（含调用的数据源、检索轮次、兜底检索情况）。

#### 5.2 标准化输出模板
```markdown
# 学术检索报告
## 一、检索汇总
- 检索主题：【用户确认的核心主题】
- 检索时间：【执行检索的时间】
- 检索范围：【时间范围+启用数据源+文献类型】
- 检索轮次：【X轮，含首轮】
- 有效检索结果：【最终输出文献数量】篇
- 执行说明：【如“全量调用arXiv、PubMed等5个平台公共API，使用内置Chromium补充检索Google Scholar、ResearchGate”】

## 二、文献详情列表
### 文献1：【文献完整标题】
- 作者：【全部作者】
- 发表时间：【年-月-日】
- 发表平台：【期刊名称/预印本平台】
- 文献标识：DOI：【有效DOI号】，全文链接：【可公开访问链接】
- 核心摘要：【300字以内精简核心研究内容、方法与结论】
- 引用格式：【用户指定的GB/T 7714/APA/MLA格式】

### 文献2：【文献完整标题】
...

## 三、主题研究综述（仅用户需求为综述/深度调研时生成）
### 3.1 领域研究现状
- 核心研究方向1：【方向名称】，关键支撑文献[1][3][5]；
- 核心研究方向2：【方向名称】，关键支撑文献[2][4][6]。

### 3.2 核心研究热点
- 高频核心关键词：【词1、词2、词3】

### 3.3 研究缺口与未来方向
- 现存研究缺口1：【缺口描述】，相关补充文献[7][8]；
- 现存研究缺口2：【缺口描述】，相关补充文献[9][10]。

## 四、参考文献（BIB格式）
```bib
【此处插入全量文献的BIB格式内容，支持直接导入Zotero/EndNote等文献管理工具】
```
```

---

### Step 6：异常兜底处理
- **全数据源无结果**：逐步放宽检索条件（去掉时间限制、简化关键词、扩大匹配范围），重新检索2次，仍无结果则向用户说明，建议调整检索主题；
- **内置Chromium调用失败**：仅使用公共API全量检索结果，向用户明确说明“部分平台未检索，结果可能存在遗漏”；
- **单平台反爬拦截**：延长请求间隔至5-10秒，重试1次，仍失败则向用户说明该平台检索受限情况，不影响其他平台结果输出；
- **多轮补全偏离主题**：立即终止补全检索，回归用户原始需求，仅输出与主题高度相关的文献。


## Key Rules 强制执行规则
1. 必须对所有用户未排除的数据源执行**全量并行检索**，不得因主观判断跳过任一数据源，不得自行设置检索优先级；
2. 必须优先使用**无密钥公开API**，仅API调用失败/无公开API时，使用内置Chromium兜底检索；
3. 必须严格按照本手册中的**API参数格式、Chromium操作步骤**执行检索，不得随意修改核心参数；
4. 必须由智能体自主完成文献去重、筛选、排序全流程，不得依赖额外代码脚本；
5. 多轮补全检索必须严格围绕用户原始需求，不得偏离主题，最多执行3轮，禁止无限循环检索；
6. 所有输出内容必须100%基于实际检索结果，禁止虚构文献信息、DOI、研究结论；
7. 必须严格遵守各平台的限流规则，禁止高频请求触发反爬。


## Essential Patterns 高频场景最佳实践
### 1. 最新前沿研究追踪
- 时间范围设为「近2年」；
- 全量检索所有预印本平台+对应领域核心数据库；
- 排序优先按「发表时间倒序」，优先展示预印本与最新见刊文献。

### 2. 经典核心文献查找
- 时间范围设为「不限」；
- 重点通过内置Chromium检索Google Scholar，提取高被引文献；
- 关键词补充「review/survey」，优先筛选领域综述类经典文献。

### 3. 引文溯源与脉络梳理
- 首轮检索定位目标核心文献；
- 多轮补全检索通过Google Scholar提取该文献的施引文献、参考文献；
- 输出时补充文献间的引用关联说明，梳理研究脉络。

### 4. 国内中文学术文献检索
- 优先通过内置Chromium全量检索必应学术、百度学术；
- 补充中英文双语关键词检索，扩大结果覆盖范围。