# Academic Full Search Skill

全量覆盖主流平台的学术搜索技能，支持多源并行检索、智能去重、引用格式生成。

## 🎯 功能特性

- **多源并行检索**: 同时搜索 arXiv, PubMed, bioRxiv, medRxiv, chemRxiv, Semantic Scholar, Google Scholar, ResearchGate
- **智能去重筛选**: 基于 DOI/标题/作者的多重去重策略
- **引用格式生成**: 支持 GB/T 7714-2015, APA, MLA 等多种格式
- **多轮深度检索**: 自动提取关键词，智能补全检索结果
- **无头浏览器兜底**: 内置 Playwright+Chromium 处理无 API 平台

## 📦 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

## ⚙️ 配置说明

1. 复制配置模板：
```bash
cp config/search_config.yaml.example config/search_config.yaml
```

2. 编辑 `config/search_config.yaml`：
```yaml
search:
  enabled_sources:
    - arxiv
    - pubmed
    - biorxiv
    - medrxiv
    - chemrxiv
    - semantic_scholar
    - google_scholar
  request_interval: 5  # 秒
  max_results: 20
  max_rounds: 3
  output_format: "GB/T 7714-2015"
  email: "your-email@example.com"  # PubMed 必需
```

## 🚀 使用示例

### 基础检索

```python
from academic_search import AcademicSearch

searcher = AcademicSearch()
results = searcher.search("machine learning in drug discovery")
```

### 高级检索

```python
results = searcher.search(
    keyword="cancer immunotherapy",
    time_range="2020-2026",
    doc_type="journal",
    exclude_sources=["researchgate"],
    output_count=30,
    citation_style="APA"
)
```

### 生成引用

```python
citation = searcher.generate_citation(results[0], style="GB/T 7714-2015")
print(citation)
```

## 📊 支持的数据源

| 数据源 | API 类型 | 限流策略 | 覆盖领域 |
|--------|---------|---------|---------|
| arXiv | 公共 API | 2 秒/请求 | 物理、计算机、数学等 |
| PubMed | 公共 API | 3 请求/秒 | 生物医学、生命科学 |
| bioRxiv | 公共 API | 2 秒/请求 | 生物学预印本 |
| medRxiv | 公共 API | 2 秒/请求 | 医学预印本 |
| chemRxiv | 公共 API | 2 秒/请求 | 化学预印本 |
| Semantic Scholar | 公共 API | 100 请求/5 分钟 | 全学科 |
| Google Scholar | 无头浏览器 | 动态调整 | 全学科 |
| ResearchGate | 无头浏览器 | 动态调整 | 全学科 |

## 📝 输出格式

### 默认输出（GB/T 7714-2015）

```
[1] Smith J, Johnson A. Machine learning in drug discovery[J/OL]. 2024. DOI: 10.1038/s41573-024-00912-3

[2] Wang L, et al. Deep learning approaches for protein structure prediction[J/OL]. 2023. DOI: 10.1016/j.cell.2023.05.020
```

### APA 格式

```
Smith, J., & Johnson, A. (2024). Machine learning in drug discovery. https://doi.org/10.1038/s41573-024-00912-3
```

## ⚠️ 注意事项

1. **PubMed 邮箱**: 使用 PubMed 时必须提供有效邮箱
2. **反爬策略**: Google Scholar/ResearchGate 可能触发验证码，建议降低检索频率
3. **时间范围**: 默认检索近 10 年文献，可通过参数调整
4. **结果去重**: 自动基于 DOI 和标题去重，确保结果唯一性

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
