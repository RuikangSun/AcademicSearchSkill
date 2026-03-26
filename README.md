# 通用学术搜索技能
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

专为智能体打造的学术搜索技能，一站式覆盖主流学术平台，支持多源并行检索、多轮深度调研、自动化反爬规避与标准化学术输出。

---

## 核心功能
- 全域多源覆盖：默认并行检索arXiv/biorxiv/chemrxiv/medrxiv/chinaxiv全系列预印本、PubMed、Google Scholar、ResearchGate等平台，自动适配学科领域
- 智能迭代调研：内置「粗搜-主题聚类-缺口补全」多轮调研逻辑，避免单次检索的信息遗漏
- 自动多策略：官方API优先→搜索引擎兜底→浏览器自动化三级方案，全程无需人工干预
- 标准化学术输出：自动去重排序，支持GB/T 7714/APA/MLA多格式标准引用生成，贴合科研使用习惯

---

## 快速开始
### 1. 部署
根据智能体技能安装要求，将本技能完整文件夹放入对应的技能仓库目录下。

### 2. 安装依赖
```bash
pip install -r requirements.txt
# 智能体通常内置了chromium组件，请使用智能体内置的chromium组件调用方式。如果没有内置的chromium组件，则通过playwright install chromium安装chromium

```

---

## 使用说明
1.  **触发规则**：对话中输入学术调研、文献查找、主题综述、文献溯源类需求，自动触发本技能，不会被通用网页搜索替代。
2.  **可自定义参数**：检索主题、时间范围、文献类型、指定/排除数据源、输出文献数量、引用格式。
3.  **标准输出结构**：检索汇总 → 文献详情列表 → 主题研究综述（按需生成） → 补充说明。

---

## 可选配置
修改`config/`目录下的yaml文件，可快速自定义：
- 数据源启用状态、优先级与学科适配规则
- 请求限流、浏览器自动化等反爬策略
- 默认输出数量、摘要长度、引用格式模板

---

## 开源协议
本项目基于 **MIT协议** 开源。