# Academic Full Search Skill

| 属性 | 值 |
|------|------|
| name | academic-full-search |
| description | 全量覆盖主流平台的学术搜索技能，支持 Crossref、arXiv、PubMed、Semantic Scholar 等。**触发规则**：用户提及"学术调研、文献查找、主题综述、参考文献、引文溯源、预印本检索、DOI 解析、GB/T 7714/APA/MLA 引用格式生成"时自动触发。**覆盖数据源**：Crossref（高优先级）、arXiv、PubMed、Semantic Scholar、bioRxiv、medRxiv、chemRxiv、Google Scholar。**禁用边界**：非学术类内容禁止调用。 |
| version | 1.3.0 |
| last_update | 2026-03-27 |
| required_env | Python 3.9+、Playwright+Chromium、requests、xmltodict、lxml、pyyaml |

---

## Prerequisites 前置检查

### 1. 环境确认

- 确认智能体已内置 Playwright 及 Chromium 无头组件
- 确认 Python 3.9+ 基础环境可用
- 安装依赖包：

```bash
pip install requests playwright xmltodict lxml pyyaml
playwright install chromium
```

### 2. 配置读取

优先读取 `config/search_config.yaml` 配置项。

**示例配置文件**（`config/search_config.yaml`）：

```yaml
search:
  enabled_sources:
    - crossref        # 高优先级 - 元数据查询
    - arxiv           # 预印本
    - pubmed          # 生物医学
    - semantic_scholar # AI 驱动学术搜索
    - biorxiv
    - medrxiv
    - chemrxiv
  
  request_interval: 2      # 秒
  max_results: 20
  max_rounds: 3
  output_format: "GB/T 7714-2015"
  email: "email@example.com"      # PubMed 必需
  mailto: "email@example.com"     # Crossref 推荐
```

---

## Workflow 标准化执行工作流

### Step 1：需求澄清（必填参数确认）

执行检索前，必须向用户确认：
- 【必填】检索核心主题/关键词/研究问题
- 【可选】时间范围（默认：近 10 年）
- 【可选】文献类型（默认：全类型）
- 【可选】排除数据源（默认：无排除）
- 【可选】输出文献数量（默认：20 篇，上限 50 篇）
- 【可选】参考文献格式（默认：GB/T 7714-2015）
- 【可选】是否限制检索轮次（默认：最多 3 轮）

---

### Step 2：全量多源并行检索（核心逻辑）

#### 2.1 检索核心原则

**对所有启用的数据源执行全量并行检索**，按优先级排序：
1. **Crossref**（高优先级 - 元数据全面、速度快）
2. **arXiv**（预印本首选）
3. **PubMed**（生物医学权威）
4. **Semantic Scholar**（AI 驱动、引用指标）
5. **bioRxiv/medRxiv/chemRxiv**（预印本补充）
6. **Google Scholar**（兜底检索）

#### 2.2 Crossref API 实现（新增 - 高优先级）

**API 端点**：`https://api.crossref.org/works`

**核心参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `query` | str | 是 | 检索关键词 | `machine learning` |
| `filter` | list | 否 | 过滤条件列表 | `["type:journal-article", "from_published_date:2020-01-01"]` |
| `sort` | str | 否 | 排序依据：`relevance`、`score`、`deposited` | `relevance` |
| `order` | str | 否 | 排序顺序：`asc`、`desc` | `desc` |
| `rows` | int | 否 | 每页结果数，默认 20，上限 1000 | `20` |
| `cursor` | str | 否 | 分页游标 | `*` |
| `mailto` | str | 推荐 | 联系邮箱（提升限流阈值） | `user@example.com` |

**常用过滤条件**：
- `type:journal-article` - 期刊论文
- `type:book-chapter` - 书籍章节
- `from_published_date:YYYY-MM-DD` - 起始日期
- `until_published_date:YYYY-MM-DD` - 结束日期
- `has-full-text:true` - 有全文
- `references:DOI` - 引用某 DOI 的文献

**示例完整代码**：

```python
import requests
import time
from datetime import datetime, timedelta

def search_crossref(keyword=None, max_results=20, filters=None, sort="relevance", order="desc", mailto=None):
    """
    检索 Crossref 元数据
    
    Args:
        keyword: 检索关键词（可选，为 None 时仅用 filter）
        max_results: 最大结果数
        filters: 过滤条件列表，如 ["type:journal-article", "from_published_date:2020-01-01"]
        sort: 排序依据
        order: 排序顺序
        mailto: 联系邮箱（推荐提供）
    
    Returns:
        list: 文献列表，包含标题、作者、DOI、出版日期等
    """
    url = "https://api.crossref.org/works"
    
    params = {
        'query': keyword if keyword else '',
        'rows': max_results,
        'sort': sort,
        'order': order
    }
    
    if filters:
        params['filter'] = filters
    
    if mailto:
        params['mailto'] = mailto
    
    # 添加 User-Agent
    headers = {
        'User-Agent': f'AcademicSearchSkill/1.3.0 (mailto:{mailto})' if mailto else 'AcademicSearchSkill/1.3.0'
    }
    
    try:
        # 遵守限流
        time.sleep(0.5)
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('message', {}).get('items', [])
        
        results = []
        for item in items:
            paper = {
                'title': item.get('title', [''])[0] if item.get('title') else '',
                'authors': [],
                'summary': item.get('abstract', ''),
                'doi': item.get('DOI', ''),
                'link': f"https://doi.org/{item.get('DOI', '')}" if item.get('DOI') else '',
                'published': '',
                'type': item.get('type', ''),
                'citations': 0,  # Crossref 不直接提供引用数
                'source': 'crossref'
            }
            
            # 作者列表
            if 'author' in item:
                for author in item['author']:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given and family:
                        paper['authors'].append(f"{given} {family}")
                    elif family:
                        paper['authors'].append(family)
            
            # 出版日期
            if 'published-print' in item or 'published-online' in item:
                pub_date = item.get('published-print') or item.get('published-online')
                if 'date-parts' in pub_date:
                    date_parts = pub_date['date-parts'][0]
                    paper['published'] = '-'.join(str(p) for p in date_parts)
            elif 'created' in item:
                # 使用创建日期作为备选
                created = item['created']
                if 'date-parts' in created:
                    date_parts = created['date-parts'][0]
                    paper['published'] = '-'.join(str(p) for p in date_parts)
            
            results.append(paper)
        
        return results
    
    except Exception as e:
        print(f"Crossref 检索失败：{e}")
        return []

# 使用示例
if __name__ == "__main__":
    papers = search_crossref(
        keyword="deep learning",
        max_results=10,
        filters=["type:journal-article", "from_published_date:2020-01-01"],
        mailto="user@example.com"
    )
    
    for p in papers:
        print(f"\n标题：{p['title']}")
        print(f"作者：{', '.join(p['authors'][:3])}...")
        print(f"DOI: {p['doi']}")
        print(f"日期：{p['published']}")
```

#### 2.3 arXiv 公共 API 实现

```python
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def search_arxiv(keyword, max_results=20, days_back=3650):
    """
    检索 arXiv 论文
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
        days_back: 回溯天数（默认 10 年）
    
    Returns:
        list: 文献列表
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    start_str = start_date.strftime("%Y%m%d0000")
    end_str = end_date.strftime("%Y%m%d0000")
    
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
        time.sleep(2)  # 遵守限流
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        results = []
        for entry in root.findall('atom:entry', ns):
            paper = {
                'title': '',
                'authors': [],
                'summary': '',
                'doi': '',
                'link': '',
                'published': '',
                'source': 'arxiv'
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
            
            published_elem = entry.find('atom:published', ns)
            if published_elem is not None:
                paper['published'] = published_elem.text[:10]
            
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    paper['link'] = link.get('href')
                    break
            
            if not paper['link']:
                arxiv_id = entry.find('atom:id', ns)
                if arxiv_id is not None:
                    arxiv_id_text = arxiv_id.text
                    if 'arxiv.org/abs/' in arxiv_id_text:
                        paper['doi'] = arxiv_id_text.split('arxiv.org/abs/')[-1]
                        paper['link'] = f"https://arxiv.org/abs/{paper['doi']}"
            
            results.append(paper)
        
        return results
    
    except Exception as e:
        print(f"arXiv 检索失败：{e}")
        return []
```

#### 2.4 PubMed E-utilities 实现

```python
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def search_pubmed(keyword, max_results=20, email="academic.search@example.com", days_back=3650):
    """
    检索 PubMed 论文
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
        email: 必需的联系邮箱
        days_back: 回溯天数
    
    Returns:
        list: 文献列表
    """
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
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
        
        root = ET.fromstring(response.content)
        id_list = root.find('IdList')
        pmids = [id_elem.text for id_elem in id_list.findall('Id')] if id_list else []
        
        if not pmids:
            return []
        
        time.sleep(0.4)  # 遵守 3 req/s 限制
        
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        efetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids[:10000]),
            'rettype': 'medline',
            'retmode': 'xml',
            'email': email
        }
        
        response = requests.get(efetch_url, params=efetch_params, timeout=60)
        response.raise_for_status()
        
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
                'pmid': '',
                'source': 'pubmed'
            }
            
            pmid_elem = article.find('.//PMID')
            if pmid_elem is not None:
                paper['pmid'] = pmid_elem.text
                paper['link'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/"
            
            title_elem = article.find('.//ArticleTitle')
            if title_elem is not None:
                paper['title'] = title_elem.text
            
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
            
            abstract_elem = article.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                paper['summary'] = abstract_elem.text or ''
            
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
            
            for id_elem in article.findall('.//ArticleId'):
                if id_elem.get('IdType') == 'doi':
                    paper['doi'] = id_elem.text
                    break
            
            results.append(paper)
        
        return results
    
    except Exception as e:
        print(f"PubMed 检索失败：{e}")
        return []
```

#### 2.5 Semantic Scholar API 实现

```python
import requests
import time

def search_semantic_scholar(keyword, max_results=20):
    """
    检索 Semantic Scholar 论文
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
    
    Returns:
        list: 文献列表
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    fields = ['title', 'authors', 'year', 'abstract', 'doi', 'citationCount', 'influentialCitationCount', 'openAccessPdf']
    
    params = {
        'query': keyword,
        'fields': ','.join(fields),
        'limit': max_results,
        'publicationDateOrYear': '2015:2026'
    }
    
    try:
        time.sleep(1)
        
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
                'link': '',
                'source': 'semantic_scholar'
            }
            
            for author in paper.get('authors', []):
                if 'name' in author:
                    result['authors'].append(author['name'])
            
            if paper.get('openAccessPdf') and paper['openAccessPdf'].get('url'):
                result['link'] = paper['openAccessPdf']['url']
            elif paper.get('doi'):
                result['link'] = f"https://doi.org/{paper['doi']}"
            else:
                paper_id = paper.get('paperId', '')
                if paper_id:
                    result['link'] = f"https://www.semanticscholar.org/paper/{paper_id}"
            
            results.append(result)
        
        return results
    
    except Exception as e:
        print(f"Semantic Scholar 检索失败：{e}")
        return []
```

#### 2.6 bioRxiv/medRxiv/chemRxiv API 实现

```python
import requests
import time
from datetime import datetime, timedelta

def search_rxiv(server, keyword, max_results=20):
    """
    检索 bioRxiv/medRxiv/chemRxiv 论文
    
    Args:
        server: 平台名称 'biorxiv', 'medrxiv' 或 'chemrxiv'
        keyword: 检索关键词
        max_results: 最大结果数
    
    Returns:
        list: 文献列表
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    url = f"https://api.medrxiv.org/details/{server}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}/0/json"
    
    try:
        time.sleep(2)
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'collection' not in data or not data['collection']:
            return []
        
        results = []
        keyword_lower = keyword.lower()
        
        for item in data['collection']:
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
                    'server': server,
                    'source': server
                }
                results.append(paper)
                
                if len(results) >= max_results:
                    break
        
        return results
    
    except Exception as e:
        print(f"{server} 检索失败：{e}")
        return []
```

#### 2.7 Google Scholar Playwright 兜底检索

```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_google_scholar(keyword, max_results=20):
    """
    使用 Playwright 爬取 Google Scholar
    
    Args:
        keyword: 检索关键词
        max_results: 最大结果数
    
    Returns:
        list: 文献列表
    """
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            await page.goto(f"https://scholar.google.com/scholar?q={keyword.replace(' ', '+')}", wait_until='domcontentloaded', timeout=30000)
            
            await page.wait_for_selector('.gs_r.gs_or.gs_scl', timeout=10000)
            
            entries = await page.query_selector_all('.gs_r.gs_or.gs_scl')
            
            for entry in entries[:max_results]:
                paper = {
                    'title': '',
                    'authors': '',
                    'summary': '',
                    'doi': '',
                    'link': '',
                    'published': '',
                    'citations': 0,
                    'source': 'google_scholar'
                }
                
                title_elem = await entry.query_selector('.gs_rt a')
                if title_elem:
                    paper['title'] = await title_elem.inner_text()
                    paper['link'] = await title_elem.get_attribute('href')
                
                author_elem = await entry.query_selector('.gs_a')
                if author_elem:
                    paper['authors'] = await author_elem.inner_text()
                
                abstract_elem = await entry.query_selector('.gs_rs')
                if abstract_elem:
                    paper['summary'] = await abstract_elem.inner_text()
                
                cite_elem = await entry.query_selector('.gs_fl a:nth-child(3)')
                if cite_elem:
                    cite_text = await cite_elem.inner_text()
                    if 'Cited by' in cite_text:
                        paper['citations'] = int(cite_text.replace('Cited by', '').strip())
                
                results.append(paper)
                await asyncio.sleep(1.5)
        
        except Exception as e:
            print(f"Google Scholar 爬取失败：{e}")
        finally:
            await browser.close()
    
    return results
```

---

### Step 3：结果标准化处理

```python
def process_results(all_results):
    """
    标准化处理检索结果：去重、筛选、排序
    """
    seen_dois = set()
    seen_titles = set()
    processed = []
    
    for paper in all_results:
        identifier = None
        
        if paper.get('doi'):
            identifier = paper['doi'].lower()
        else:
            title = paper.get('title', '').lower().strip()
            year = paper.get('published', '')[:4]
            authors = paper.get('authors', [])
            first_author = authors[0].split()[-1] if authors else 'Unknown'
            identifier = f"{title}_{year}_{first_author}"
        
        if identifier in seen_dois or identifier in seen_titles:
            continue
        
        if not paper.get('title') or paper['title'] in ['', '[Title not available]']:
            continue
        
        if not paper.get('link') and not paper.get('doi'):
            continue
        
        seen_dois.add(identifier)
        if paper.get('title'):
            seen_titles.add(paper['title'].lower().strip())
        
        processed.append(paper)
    
    processed.sort(key=lambda x: (
        x.get('citations', 0),
        x.get('published', '')
    ), reverse=True)
    
    return processed
```

---

### Step 4：多轮深度补全检索

使用自然语言处理提取关键词，生成新的检索词组合，重复 Step2-Step3 流程。

---

### Step 5：标准输出与交付

```python
def generate_citation(paper, style="GB/T 7714-2015"):
    """
    生成标准引用格式
    """
    authors = paper.get('authors', [])
    title = paper.get('title', '')
    year = paper.get('published', '')[:4] if paper.get('published') else ''
    doi = paper.get('doi', '')
    
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

1. 必须对所有用户未排除的数据源执行**全量并行检索**
2. 必须优先使用**无密钥公开 API**（Crossref > arXiv > PubMed > Semantic Scholar）
3. 必须严格遵守各平台的限流规则
4. 所有输出内容必须 100% 基于实际检索结果，禁止虚构文献信息
5. Crossref 作为高优先级数据源，应优先调用以获取全面元数据

---

## Essential Patterns 高频场景最佳实践

| 场景 | 推荐数据源组合 | 关键参数 |
|------|---------------|----------|
| DOI 解析 | Crossref（首选） | 精确匹配 DOI |
| 最新前沿追踪 | arXiv + bioRxiv + Crossref | 时间范围：近 2 年 |
| 经典文献查找 | Crossref + PubMed + Semantic Scholar | 按引用排序 |
| 交叉学科研究 | 全平台并行 | 多组关键词组合 |
| 中文学术 | Crossref + Semantic Scholar | 中英双语关键词 |
