"""
多轮迭代学术搜索核心脚本
适配OpenAkita Agent调用规范
"""
from scripts.multi_source_parallel import multi_source_search
from utils.literature_clustering import literature_clustering, gap_analysis
from utils.keyword_process import keyword_optimization
from scripts.deduplication_and_sort import deduplication_and_sort

def iteration_search(user_params: dict) -> dict:
    """
    多轮迭代搜索主函数
    :param user_params: 用户需求解析后的参数字典
    :return: 最终检索结果与迭代详情
    """
    max_rounds = user_params.get("max_rounds", 3)
    current_round = 1
    all_literatures = []
    iteration_details = []

    # 第一轮：全域粗搜
    print(f"===== 执行第{current_round}轮全域粗搜 =====")
    round1_result = multi_source_search(
        keywords=user_params["keywords"],
        data_sources=user_params["data_sources"],
        max_results=user_params["default_max_results"]
    )
    all_literatures.extend(round1_result["literatures"])
    iteration_details.append({
        "round": current_round,
        "keywords": user_params["keywords"],
        "literature_count": len(round1_result["literatures"]),
        "data_sources": round1_result["data_sources"]
    })

    # 去重与聚类
    all_literatures = deduplication_and_sort(all_literatures)
    cluster_result = literature_clustering(all_literatures)

    # 缺口分析
    gap_result = gap_analysis(cluster_result, user_params)
    has_gap = gap_result["has_gap"]

    # 迭代循环
    while has_gap and current_round < max_rounds:
        current_round += 1
        print(f"===== 执行第{current_round}轮精准定向搜索 =====")

        # 关键词优化
        optimized_keywords = keyword_optimization(
            original_keywords=user_params["keywords"],
            gap_info=gap_result,
            cluster_keywords=cluster_result["core_keywords"]
        )

        # 定向数据源检索
        round_result = multi_source_search(
            keywords=optimized_keywords,
            data_sources=gap_result["target_data_sources"],
            max_results=user_params["default_max_results"] // 2
        )

        # 结果合并与去重
        all_literatures.extend(round_result["literatures"])
        all_literatures = deduplication_and_sort(all_literatures)

        # 迭代详情记录
        iteration_details.append({
            "round": current_round,
            "keywords": optimized_keywords,
            "literature_count": len(round_result["literatures"]),
            "data_sources": round_result["data_sources"],
            "target_gap": gap_result["gap_description"]
        })

        # 重新聚类与缺口分析
        cluster_result = literature_clustering(all_literatures)
        gap_result = gap_analysis(cluster_result, user_params)
        has_gap = gap_result["has_gap"]

    # 结果返回
    return {
        "user_params": user_params,
        "iteration_details": iteration_details,
        "final_literatures": all_literatures[:user_params["output_count"]],
        "cluster_result": cluster_result,
        "gap_feedback": gap_result["gap_description"] if has_gap else "无核心信息缺口"
    }

if __name__ == "__main__":
    # 测试示例
    test_params = {
        "keywords": "large language model drug discovery",
        "data_sources": ["arxiv", "pubmed", "chemrxiv", "google_scholar"],
        "default_max_results": 15,
        "output_count": 15,
        "max_rounds": 3,
        "subject": "chemistry"
    }
    result = iteration_search(test_params)
    print(f"迭代完成，最终有效文献数量：{len(result['final_literatures'])}")