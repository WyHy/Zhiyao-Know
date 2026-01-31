"""
检查图谱数据一致性
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge.adapters.upload import UploadGraphAdapter


async def main():
    print("=== 检查图谱数据一致性 ===\n")

    adapter = UploadGraphAdapter()

    # 查询数据
    result = await adapter.query_nodes(keyword="*", max_nodes=100)

    nodes = result.get("nodes", [])
    edges = result.get("edges", [])

    print(f"节点总数: {len(nodes)}")
    print(f"边总数: {len(edges)}")

    # 构建节点 ID 集合
    node_ids = {node["id"] for node in nodes}
    print(f"\n节点 ID 集合大小: {len(node_ids)}")

    # 检查边的端点是否都在节点列表中
    missing_sources = []
    missing_targets = []

    for i, edge in enumerate(edges):
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")

        if source_id not in node_ids:
            missing_sources.append((i, source_id, edge.get("type")))

        if target_id not in node_ids:
            missing_targets.append((i, target_id, edge.get("type")))

    # 报告结果
    print(f"\n=== 数据一致性检查结果 ===")
    print(f"缺失源节点的边数: {len(missing_sources)}")
    print(f"缺失目标节点的边数: {len(missing_targets)}")

    if missing_sources:
        print(f"\n前5个缺失源节点的边:")
        for idx, source_id, edge_type in missing_sources[:5]:
            print(f"  边 #{idx}: source_id='{source_id}', type='{edge_type}'")

    if missing_targets:
        print(f"\n前5个缺失目标节点的边:")
        for idx, target_id, edge_type in missing_targets[:5]:
            print(f"  边 #{idx}: target_id='{target_id}', type='{edge_type}'")

    # 统计边的类型分布
    edge_types = {}
    for edge in edges:
        edge_type = edge.get("type", "未知")
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    print(f"\n=== 边类型分布 ===")
    for edge_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
        print(f"  {edge_type}: {count}")

    # 如果有不一致，建议解决方案
    if missing_sources or missing_targets:
        print("\n⚠️ 发现数据不一致！")
        print("建议：增加 max_nodes 参数，或者修改查询逻辑确保边的端点节点都被包含。")
    else:
        print("\n✅ 数据一致性检查通过！所有边的端点节点都存在。")


if __name__ == "__main__":
    asyncio.run(main())
