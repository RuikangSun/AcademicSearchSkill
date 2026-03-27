# Academic Full Search Skill 

|------|------|
| name | academic-full-search |
| description | 全量覆盖主流平台的学术搜索技能。**触发规则**：用户提及"学术调研、文献查找、主题综述、参考文献、引文溯源、预印本检索、GB/T 7714/APA/MLA引用格式生成"时自动触发，禁止被通用网页搜索替代。**覆盖数据源**：arXiv、bioRxiv、chemRxiv、medRxiv、PubMed、Google Scholar、Semantic Scholar、ResearchGate。**禁用边界**：非学术类内容禁止调用。 |
| version | 1.2.0 |
| last_update | 2026-03-27 |
| required_env | Python 3.9+基础环境、智能体内置Playwright+Chromium组件、requests 库 |

## Prerequisites 前置检查

### 1. 环境确认
- 确认智能体已内置Playwright及Chromium无头组件（无需用户额外安装）；
- 确认Python 3.9+基础环境可用，需要安装以下依赖包：

```bash
pip install requests playwright xmltodict lxml pyyaml
playwright install chromium
```

### 2. 配置读取
优先读取`config/search_config.yaml`中的配置项，无配置文件时，默认启用本手册中全部数据源、最大3轮检索、单平台请求间隔≥5秒的基础规则。

**示例配置文件**（`config/search_config.yaml`）：

```yaml
search:
  enabled_sources:
    - arxiv
    - biorxiv
    - medrxiv
    - chemrxiv
    - pubmed
    - google_scholar
    - semantic_scholar
    - researchgate
  request_interval: 5  # 秒
  max_results: 20
  max_rounds: 3
  output_format: "GB/T 7714-2015"
  email: "email@example.com"  # PubMed必需
```

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

- **时间范围过滤**：通过`search_query`中的`submittedDate`字段实现，格式为`[YYYYMMDDTTTT+TO+YYYYMMDDTTTT]`（TTTT为24小时制分钟，GMT时区）
  示例：`submittedDate:[201601010000+TO+202603260000]`

- **示例完整请求**：
```python
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def search_arxiv(keyword, max_results=20, days_back=3650):
    """
    检索arXiv论文
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
        days_back: 回溯天数（默认10年）
    
    Returns:
        list: 文献列表，每项包含标题、作者、摘要、DOI、链接、日期
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # 格式化日期
    start_str = start_date.strftime("%Y%m%d0000")
    end_str = end_date.strftime("%Y%m%d0000")
    
    # 构造查询
    query = f'all:{keyword.replace(" ", "+")}+AND+submittedDate:[{start_str}+TO+{end_str}]'
    
    url = "http://export.arxiv.org/api/query"
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    try:
        # 遵守2秒限流
        time.sleep(2)
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # 解析XML
        root = ET.fromstring(response.content)
        
        # 获取命名空间
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        results = []
        for entry in root.findall('atom:entry', ns):
            paper = {
                'title': '',
                'authors': [],
                'summary': '',
                'doi': '',
                'link': '',
                'published': ''
            }
            
            title_elem = entry.find('atom:title', ns)
            if title_elem is not None:
                paper['title'] = title_elem.text.strip()
            
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    paper['authors'].append(name_elem.text)
            
            summary_elem = entry.find('atom:summary', ns)
            if summary_elem is not None:
                paper['summary'] = summary_elem.text.strip()
            
            # 获取发布日期
            published_elem = entry.find('atom:published', ns)
            if published_elem is not None:
                paper['published'] = published_elem.text[:10]  # 取YYYY-MM-DD
            
            # 获取PDF链接
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    paper['link'] = link.get('href')
                    break
            
            # 从链接提取arXiv ID作为DOI替代
            if not paper['doi'] and paper['link']:
                arxiv_id = entry.find('atom:id', ns)
                if arxiv_id is not None:
                    arxiv_id_text = arxiv_id.text
                    if 'arxiv.org/abs/' in arxiv_id_text:
                        paper['doi'] = arxiv_id_text.split('arxiv.org/abs/')[-1]
            
            results.append(paper)
        
        return results
    except Exception as e:
        print(f"arXiv检索失败: {e}")
        return []

# 使用示例
if __name__ == "__main__":
    papers = search_arxiv("machine learning", max_results=10)
    for p in papers:
        print(f"\n标题: {p['title']}")
        print(f"作者: {', '.join(p['authors'][:3])}...")
        print(f"日期: {p['published']}")
        print(f"链接: {p['link']}")
```

##### 2.2.2 PubMed E-utilities公共API实现

- **核心流程**：先用`ESearch`检索获取PMID列表，再用`EFetch`批量获取文献详情。

**ESearch API（检索PMID）**：
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

**EFetch API（获取文献详情）**：
- **端点**：`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
- **核心参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `db` | str | 是 | 固定为`pubmed` | `pubmed` |
| `id` | str | 是 | 用逗号分隔的PMID列表 | `38000001,38000002` |
| `rettype` | str | 是 | 返回类型：`abstract`（摘要）、`medline`（完整元数据） | `medline` |
| `retmode` | str | 是 | 返回格式：`xml`、`text` | `xml` |
| `email` | str | 是 | 同ESearch | `academic.search@example.com` |

- **限流规则**：无API密钥时≤3 req/s，单EFetch请求PMID数≤10000。

**示例完整代码**：
```python
import requests
import time
import xml.etree.ElementTree as ET

def search_pubmed(keyword, max_results=20, email="academic.search@example.com", days_back=3650):
    """
    检索PubMed论文
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
        email: 必需的联系邮箱
        days_back: 回溯天数
    
    Returns:
        list: 文献列表
    """
    # Step 1: ESearch获取PMID
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # 构造日期过滤条件
    date_filter = f"{start_date.strftime('%Y/%m/%d')}[DP]:{end_date.strftime('%Y/%m/%d')}[DP]"
    
    esearch_params = {
        'db': 'pubmed',
        'term': f'{keyword}[TI/AB] AND {date_filter}',
        'retmax': max_results,
        'retstart': 0,
        'sort': 'date',
        'rettype': 'xml',
        'email': email,
        'tool': 'AcademicSearchSkill'
    }
    
    try:
        response = requests.get(esearch_url, params=esearch_params, timeout=30)
        response.raise_for_status()
        
        # 解析PMID列表
        root = ET.fromstring(response.content)
        id_list = root.find('IdList')
        pmids = [id_elem.text for id_elem in id_list.findall('Id')] if id_list else []
        
        if not pmids:
            return []
        
        # Step 2: EFetch获取详情
        # 遵守3 req/s限制
        time.sleep(0.4)
        
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        efetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids[:10000]),  # PubMed限制
            'rettype': 'medline',
            'retmode': 'xml',
            'email': email
        }
        
        response = requests.get(efetch_url, params=efetch_params, timeout=60)
        response.raise_for_status()
        
        # 解析文献详情
        root = ET.fromstring(response.content)
        results = []
        
        for article in root.findall('.//PubmedArticle'):
            paper = {
                'title': '',
                'authors': [],
                'summary': '',
                'doi': '',
                'link': '',
                'published': '',
                'pmid': ''
            }
            
            # PMID
            pmid_elem = article.find('.//PMID')
            if pmid_elem is not None:
                paper['pmid'] = pmid_elem.text
                paper['link'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/"
            
            # 标题
            title_elem = article.find('.//ArticleTitle')
            if title_elem is not None:
                paper['title'] = title_elem.text
            
            # 作者列表
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('Author'):
                    last_name = author.find('LastName')
                    fore_name = author.find('ForeName')
                    if last_name is not None:
                        name = last_name.text
                        if fore_name is not None:
                            name = f"{fore_name.text} {name}"
                        paper['authors'].append(name)
            
            # 摘要
            abstract_elem = article.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                paper['summary'] = abstract_elem.text or ''
            
            # 发表日期
            pub_date = article.find('.//PubDate')
            if pub_date is not None:
                year = pub_date.find('Year')
                month = pub_date.find('Month')
                day = pub_date.find('Day')
                date_parts = []
                if year is not None:
                    date_parts.append(year.text)
                if month is not None:
                    date_parts.append(month.text)
                if day is not None:
                    date_parts.append(day.text)
                paper['published'] = '-'.join(date_parts)
            
            # DOI
            for id_elem in article.findall('.//ArticleId'):
                if id_elem.get('IdType') == 'doi':
                    paper['doi'] = id_elem.text
                    break
            
            results.append(paper)
        
        return results
    except Exception as e:
        print(f"PubMed检索失败: {e}")
        return []

# 使用示例
if __name__ == "__main__":
    papers = search_pubmed("cancer immunotherapy", max_results=10)
    for p in papers:
        print(f"\nPMID: {p['pmid']}")
        print(f"标题: {p['title']}")
        print(f"作者: {', '.join(p['authors'][:3])}...")
        print(f"DOI: {p['doi']}")
```

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

- **关键词过滤**：API不直接支持关键词检索，需先获取日期范围内的文献元数据，再由智能体在本地通过标题/摘要匹配关键词；
- **限流规则**：单请求间隔≥2秒。

**示例完整代码**：
```python
import requests
import time
import re

def search_rxiv(server, keyword, max_results=20):
    """
    检索bioRxiv/medRxiv/chemRxiv论文
    
    Args:
        server: 平台名称 'biorxiv', 'medrxiv' 或 'chemrxiv'
        keyword: 检索关键词
        max_results: 最大结果数
    
    Returns:
        list: 文献列表
    """
    # 构造API URL（获取最近一年的文献）
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    url = f"https://api.medrxiv.org/details/{server}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}/0/json"
    
    try:
        time.sleep(2)  # 遵守限流
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'collection' not in data or not data['collection']:
            return []
        
        results = []
        keyword_lower = keyword.lower()
        
        for item in data['collection']:
            # 本地关键词过滤
            title = item.get('title', '').lower()
            abstract = item.get('abstract', '').lower()
            
            if keyword_lower in title or keyword_lower in abstract:
                paper = {
                    'title': item.get('title', ''),
                    'authors': item.get('authors', 'N/A').split('; ') if 'authors' in item else [],
                    'summary': item.get('abstract', ''),
                    'doi': item.get('doi', ''),
                    'link': f"https://doi.org/{item.get('doi', '')}",
                    'published': item.get('date', ''),
                    'server': server
                }
                results.append(paper)
                
                if len(results) >= max_results:
                    break
        
        return results
    except Exception as e:
        print(f"{server}检索失败: {e}")
        return []

# 使用示例
if __name__ == "__main__":
    # 同时检索三个平台
    for server in ['biorxiv', 'medrxiv', 'chemrxiv']:
        print(f"\n{'='*50}")
        print(f"检索 {server}...")
        papers = search_rxiv(server, "neural networks", max_results=5)
        for p in papers:
            print(f"\n标题: {p['title'][:80]}...")
            print(f"日期: {p['published']}")
```

##### 2.2.4 Semantic Scholar公共API实现（新增）

- **API端点**：`https://api.semanticscholar.org/graph/v1/paper/search`
- **核心参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `query` | str | 是 | 检索关键词 | `machine learning` |
| `fields` | str | 是 | 返回字段，逗号分隔 | `title,authors,year,abstract,doi,citationCount` |
| `limit` | int | 否 | 返回数量，默认10，上限100 | `20` |
| `publicationDateOrYear` | str | 否 | 年份过滤 | `2020:2026` |

- **返回格式**：JSON，包含论文标题、作者、年份、摘要、DOI、引用数等；
- **限流规则**：单次请求≤100条，频率限制较为宽松（约100 req/5min）。

**示例完整代码**：
```python
import requests
import time

def search_semantic_scholar(keyword, max_results=20):
    """
    检索Semantic Scholar论文
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
    
    Returns:
        list: 文献列表
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # 请求字段
    fields = ['title', 'authors', 'year', 'abstract', 'doi', 
              'citationCount', 'influentialCitationCount', 'openAccessPdf']
    
    params = {
        'query': keyword,
        'fields': ','.join(fields),
        'limit': max_results,
        'publicationDateOrYear': '2015:2026'  # 近10年
    }
    
    try:
        time.sleep(1)  # 礼貌性延迟
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for paper in data.get('data', []):
            result = {
                'title': paper.get('title', ''),
                'authors': [],
                'summary': paper.get('abstract', ''),
                'doi': paper.get('doi', ''),
                'published': str(paper.get('year', '')),
                'citations': paper.get('citationCount', 0),
                'link': ''
            }
            
            # 提取作者姓名
            for author in paper.get('authors', []):
                if 'name' in author:
                    result['authors'].append(author['name'])
            
            # 优先使用OpenAccess PDF链接
            if paper.get('openAccessPdf') and paper['openAccessPdf'].get('url'):
                result['link'] = paper['openAccessPdf']['url']
            elif paper.get('doi'):
                result['link'] = f"https://doi.org/{paper['doi']}"
            else:
                # 构造Semantic Scholar页面链接
                paper_id = paper.get('paperId', '')
                if paper_id:
                    result['link'] = f"https://www.semanticscholar.org/paper/{paper_id}"
            
            results.append(result)
        
        return results
    except Exception as e:
        print(f"Semantic Scholar检索失败: {e}")
        return []

# 使用示例
if __name__ == "__main__":
    papers = search_semantic_scholar("deep learning", max_results=10)
    for p in papers:
        print(f"\n标题: {p['title'][:80]}...")
        print(f"年份: {p['published']}, 引用: {p['citations']}")
        print(f"开放获取: {'是' if p['link'] and 'pdf' in p['link'] else '否'}")
```

#### 2.3 第二阶段：内置Chromium全量兜底检索

对无公开无密钥API、API调用失败、访问受限的数据源，同步使用智能体内置Chromium无头模式执行检索，不得随意跳过任一启用的数据源。

##### 2.3.1 覆盖范围
Google Scholar、ResearchGate等无公开稳定API的平台。

##### 2.3.2 通用Chromium检索操作步骤

```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_google_scholar(keyword, max_results=20):
    """
    使用Playwright爬取Google Scholar
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
    
    Returns:
        list: 文献列表
    """
    results = []
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # 访问Google Scholar
            await page.goto(f"https://scholar.google.com/scholar?q={keyword.replace(' ', '+')}",
                           wait_until='domcontentloaded', timeout=30000)
            
            # 等待结果加载
            await page.wait_for_selector('.gs_r.gs_or.gs_scl', timeout=10000)
            
            # 提取结果
            entries = await page.query_selector_all('.gs_r.gs_or.gs_scl')
            
            for entry in entries[:max_results]:
                paper = {
                    'title': '',
                    'authors': '',
                    'summary': '',
                    'doi': '',
                    'link': '',
                    'published': '',
                    'citations': 0
                }
                
                # 标题
                title_elem = await entry.query_selector('.gs_rt a')
                if title_elem:
                    paper['title'] = await title_elem.inner_text()
                    paper['link'] = await title_elem.get_attribute('href')
                
                # 作者/期刊信息
                author_elem = await entry.query_selector('.gs_a')
                if author_elem:
                    paper['authors'] = await author_elem.inner_text()
                
                # 摘要
                abstract_elem = await entry.query_selector('.gs_rs')
                if abstract_elem:
                    paper['summary'] = await abstract_elem.inner_text()
                
                # 被引量
                cite_elem = await entry.query_selector('.gs_fl a:nth-child(3)')
                if cite_elem:
                    cite_text = await cite_elem.inner_text()
                    if 'Cited by' in cite_text:
                        paper['citations'] = int(cite_text.replace('Cited by', '').strip())
                
                results.append(paper)
                
                # 随机延迟避免反爬
                await asyncio.sleep(1.5)
        
        except Exception as e:
            print(f"Google Scholar爬取失败: {e}")
        
        finally:
            await browser.close()
    
    return results

# 使用示例
if __name__ == "__main__":
    papers = asyncio.run(scrape_google_scholar("neural networks", max_results=10))
    for p in papers:
        print(f"\n标题: {p['title'][:80]}")
        print(f"作者: {p['authors']}")
        print(f"引用: {p['citations']}")
```

---

### Step 3：结果标准化处理

**去重+筛选+排序代码示例**：
```python
def process_results(all_results):
    """
    标准化处理检索结果：去重、筛选、排序
    """
    seen_dois = set()
    seen_titles = set()
    processed = []
    
    for paper in all_results:
        # 生成唯一标识
        identifier = None
        
        if paper.get('doi'):
            identifier = paper['doi'].lower()
        else:
            # 无DOI时使用"标题+年份+第一作者"作为标识
            title = paper.get('title', '').lower().strip()
            year = paper.get('published', '')[:4]
            authors = paper.get('authors', [])
            first_author = authors[0].split()[-1] if authors else 'Unknown'
            identifier = f"{title}_{year}_{first_author}"
        
        # 去重检查
        if identifier in seen_dois or identifier in seen_titles:
            continue
        
        # 有效性筛选
        if not paper.get('title') or paper['title'] in ['', '[Title not available]']:
            continue
        
        if not paper.get('link') and not paper.get('doi'):
            continue  # 无访问链接
        
        seen_dois.add(identifier)
        if paper.get('title'):
            seen_titles.add(paper['title'].lower().strip())
        
        processed.append(paper)
    
    # 排序：按引用数(降序) + 发表时间(降序)
    processed.sort(key=lambda x: (
        x.get('citations', 0),
        x.get('published', '')
    ), reverse=True)
    
    return processed
```

---

### Step 4：多轮深度补全检索

使用自然语言处理提取关键词，生成新的检索词组合，重复Step2-Step3流程。

---

### Step 5：标准输出与交付

**参考文献格式生成代码示例**：
```python
def generate_citation(paper, style="GB/T 7714-2015"):
    """
    生成标准引用格式
    """
    authors = paper.get('authors', [])
    title = paper.get('title', '')
    year = paper.get('published', '')[:4] if paper.get('published') else ''
    doi = paper.get('doi', '')
    
    # 格式化作者
    if isinstance(authors, list):
        if len(authors) <= 3:
            author_str = ', '.join(authors)
        else:
            author_str = f"{authors[0]} 等"
    else:
        author_str = authors
    
    if style == "GB/T 7714-2015":
        return f"[{author_str}]. {title}[J/OL]. {year}. DOI: {doi}"
    elif style == "APA":
        return f"{author_str} ({year}). {title}. https://doi.org/{doi}"
    elif style == "MLA":
        return f'{author_str}. "{title}." ({year}).'
    else:
        return f"{author_str}. {title}. {year}."
```

---

## Key Rules 强制执行规则

1. 必须对所有用户未排除的数据源执行**全量并行检索**；
2. 必须优先使用**无密钥公开API**，仅API调用失败/无公开API时，使用内置Chromium兜底检索；
3. 必须严格遵守各平台的限流规则；
4. 所有输出内容必须100%基于实际检索结果，禁止虚构文献信息。

## Essential Patterns 高频场景最佳实践

| 场景 | 推荐数据源组合 | 关键参数 |
|------|---------------|----------|
| 最新前沿追踪 | arXiv + bioRxiv系列 + Semantic Scholar | 时间范围：近2年，按时间排序 |
| 经典文献查找 | PubMed + Google Scholar + Semantic Scholar | 不限时间，按引用排序 |
| 交叉学科研究 | 全平台并行 | 多组关键词组合 |
| 中文学术 | Semantic Scholar + Google Scholar + 百度学术 | 中英双语关键词 |
