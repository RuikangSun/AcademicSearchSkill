# Academic Full Search Skill

全量覆盖主流平台的学术搜索技能，支持多源并行检索、智能去重、标准引用格式生成。

![Version](https://img.shields.io/badge/version-1.3.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)

---

## 📌 特性

- **全平台覆盖**：支持 arXiv、PubMed、Crossref、Semantic Scholar、bioRxiv/medRxiv/chemRxiv、Google Scholar 等主流学术平台
- **并行检索**：多数据源同时检索，最大化覆盖相关文献
- **智能去重**：基于 DOI、标题、作者等多维度去重
- **标准引用**：支持 GB/T 7714-2015、APA、MLA 等多种引用格式
- **多轮补全**：自动提取关键词进行多轮深度检索
- **无密钥优先**：优先使用公开 API，无需注册即可使用

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Playwright + Chromium（智能体内置）
- 依赖包：`requests`, `playwright`, `xmltodict`, `lxml`, `pyyaml`

### 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 基础使用

```python
from academic_search import AcademicSearch

# 初始化搜索器
searcher = AcademicSearch()

# 执行搜索
results = searcher.search(
    keyword="machine learning",
    max_results=20,
    days_back=3650,
    enabled_sources=["arxiv", "pubmed", "crossref", "semantic_scholar"]
)

# 生成引用
for paper in results:
    print(searcher.generate_citation(paper, style="GB/T 7714-2015"))
```

---

## 📊 支持的数据源

| 数据源 | 类型 | API 类型 | 覆盖领域 | 优先级 |
|--------|------|---------|---------|--------|
| **Crossref** | 元数据 | 公开 API | 全学科 | ⭐⭐⭐⭐⭐ |
| **arXiv** | 预印本 | 公开 API | 物理、计算机、数学等 | ⭐⭐⭐⭐⭐ |
| **PubMed** | 摘要索引 | 公开 API | 生物医学 | ⭐⭐⭐⭐⭐ |
| **Semantic Scholar** | 元数据 | 公开 API | 全学科 | ⭐⭐⭐⭐ |
| **bioRxiv** | 预印本 | 公开 API | 生物学 | ⭐⭐⭐⭐ |
| **medRxiv** | 预印本 | 公开 API | 医学 | ⭐⭐⭐⭐ |
| **chemRxiv** | 预印本 | 公开 API | 化学 | ⭐⭐⭐⭐ |
| **Google Scholar** | 搜索引擎 | Playwright 爬取 | 全学科 | ⭐⭐⭐ |

### 数据源说明

#### Crossref（高优先级）
- **优势**：覆盖 1.4 亿+ 学术作品元数据，提供 DOI 解析、引用关系、基金信息等
- **API**：`https://api.crossref.org/works`
- **特点**：查询速度快、数据结构化程度高、支持复杂过滤
- **限流**：建议添加 `mailto` 参数标识身份

#### arXiv
- **优势**：最新预印本，涵盖物理、计算机、数学等领域
- **API**：`http://export.arxiv.org/api/query`
- **特点**：支持学科分类过滤、按时间排序

#### PubMed
- **优势**：生物医学领域最权威摘要库
- **API**：ESearch + EFetch
- **特点**：需配合邮箱使用，支持 MeSH 术语

#### Semantic Scholar
- **优势**：AI 驱动，提供引用数、影响力等指标
- **API**：`https://api.semanticscholar.org/graph/v1/paper/search`
- **特点**：开放获取标识、引用关系清晰

---

## 📋 配置说明

### 配置文件

创建 `config/search_config.yaml`：

```yaml
search:
  enabled_sources:
    - crossref      # 高优先级
    - arxiv
    - pubmed
    - semantic_scholar
    - biorxiv
    - medrxiv
    - chemrxiv
  
  request_interval: 2       # 请求间隔（秒）
  max_results: 20           # 单平台最大结果数
  max_rounds: 3             # 最大检索轮次
  output_format: "GB/T 7714-2015"
  
  # PubMed 必需
  email: "your.email@example.com"
  
  # Crossref 推荐（非必需但建议）
  mailto: "your.email@example.com"
```

### 环境变量（可选）

```bash
export CROSSREF_MAILTO="your.email@example.com"
export PUBMED_EMAIL="your.email@example.com"
```

---

## 🔧 高级用法

### 1. 自定义过滤条件

```python
# Crossref 高级过滤
results = searcher.search_crossref(
    query="machine learning",
    filter=[
        "type:journal-article",
        "from_published_date:2020-01-01",
        "until_published_date:2024-12-31"
    ],
    sort="relevance",
    order="desc"
)
```

### 2. DOI 解析

```python
# 通过 DOI 获取元数据
paper = searcher.resolve_doi("10.1038/nature12373")
print(paper['title'])
print(paper['authors'])
```

### 3. 引用关系查询

```python
# 查询引用了某篇文献的文章
citations = searcher.search_crossref(
    query=None,
    filter=["references:10.1038/nature12373"]
)
```

### 4. 多关键词组合检索

```python
keywords = ["deep learning", "neural networks", "transformers"]
all_results = []

for kw in keywords:
    results = searcher.search(keyword=kw, max_results=10)
    all_results.extend(results)

# 去重
unique_results = searcher.process_results(all_results)
```

---

## 📄 输出格式

### 标准引用格式

```python
# GB/T 7714-2015
"[1] Goodfellow I, Bengio Y, Courville A. Deep Learning[M]. MIT Press, 2016."

# APA
"Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep Learning. MIT Press."

# MLA
"Goodfellow, Ian, et al. Deep Learning. MIT Press, 2016."
```

### JSON 格式

```json
{
  "title": "Deep Learning",
  "authors": ["Goodfellow, Ian", "Bengio, Yoshua", "Courville, Aaron"],
  "year": "2016",
  "doi": "10.1038/nature12373",
  "link": "https://doi.org/10.1038/nature12373",
  "citations": 15000,
  "source": "crossref"
}
```

---

## 🎯 最佳实践

| 场景 | 推荐数据源组合 | 关键参数 |
|------|---------------|---------|
| 最新前沿追踪 | arXiv + bioRxiv + Crossref | 时间范围：近 2 年 |
| 经典文献查找 | Crossref + PubMed + Semantic Scholar | 按引用数排序 |
| 交叉学科研究 | 全平台并行 | 多组关键词 |
| DOI 解析 | Crossref（首选） | 精确匹配 |
| 中文学术 | Crossref + Semantic Scholar | 中英双语关键词 |

---

## ⚠️ 注意事项

1. **礼貌访问**：建议添加 `mailto` 参数标识身份，避免被限流
2. **频率控制**：遵守各平台限流规则（Crossref 建议≤3 req/s）
3. **数据缓存**：建议缓存已查询结果，避免重复请求
4. **反爬机制**：Google Scholar 可能触发验证，建议优先使用 API 数据源

---

## 📝 更新日志

### v1.3.0 (2026-03-27)
- ✨ **新增 Crossref 数据源**（高优先级）
  - 支持 DOI 解析、元数据查询、引用关系
  - 添加复杂过滤条件支持
  - 优化查询速度和数据结构
- 🔄 调整数据源优先级排序
- 📝 完善配置示例

### v1.2.0 (2026-03-27)
- ✨ 新增 Semantic Scholar 数据源
- 🗑️ 移除 chinaxiv 数据源
- 📝 添加完整 Python 代码示例

### v1.1.0 (2026-03-26)
- 初始版本发布

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 📬 联系方式

- 问题反馈：https://github.com/RuikangSun/AcademicSearchSkill/issues
- 示例项目：https://github.com/RuikangSun/AcademicSearchSkill
