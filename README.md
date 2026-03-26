# AcademicSearchSkill
全量覆盖主流平台的轻量化学术搜索技能，专为智能体设计，无需密钥即可使用，支持公共API检索与内置Chromium兜底。

## 功能特性
- **全数据源覆盖**：arXiv、PubMed、预印本、Google Scholar、ResearchGate
- **双模式智能检索**：优先无密钥公共API，失败时自动切换内置Chromium兜底
- **自主结果处理**：智能体独立完成去重、筛选、排序，无需额外代码
- **多轮深度补全**：自动识别新关键词/研究方向，补充检索相关文献
- **标准化学术输出**：支持GB/T 7714/APA/MLA引用格式，生成可导入文献管理工具的BIB文件

## 快速开始
### 前置要求
- Python 3.9+ 基础环境
- 智能体内置Playwright+Chromium组件（无需用户额外安装）
