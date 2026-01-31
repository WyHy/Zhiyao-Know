"""
测试图谱查询，检查是否有孤立节点
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge.adapters.upload import UploadGraphAdapter


async def main():
    print("=== 测试图谱查询（检查孤立节点）===\n")

    adapter = UploadGraphAdapter()

    # 查询 100 个节点
    result = await adapter.query_nodes(keyword="*", max_nodes=100)

    nodes = result.get("nodes", [])
    edges = result.get("edges", [])

    print(f"返回的节点数: {len(nodes)}")
    print(f"返回的边数: {len(edges)}")

    # 构建节点 ID 到节点的映射
    node_map = {node["id"]: node for node in nodes}

    # 检查每个节点的连接情况
    node_connections = {node_id: 0 for node_id in node_map.keys()}

    for edge in edges:
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")

        if source_id in node_connections:
            node_connections[source_id] += 1
        if target_id in node_connections:
            node_connections[target_id] += 1

    # 找出孤立节点（连接数为0）
    isolated_nodes = [
        (node_id, node_map[node_id].get("name")) 
        for node_id, count in node_connections.items() 
        if count == 0
    ]

    print(f"\n孤立节点数量: {len(isolated_nodes)}")

    if isolated_nodes:
        print("\n孤立节点列表:")
        for node_id, node_name in isolated_nodes[:10]:
            print(f"  - 名称: {node_name}")
            print(f"    ID: {node_id}")
    else:
        print("\n✅ 没有孤立节点！所有节点都有连接。")

    # 检查是否有边引用了不存在的节点
    print("\n=== 检查边的完整性 ===")
    missing_sources = []
    missing_targets = []

    for edge in edges:
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")

        if source_id not in node_map:
            missing_sources.append(source_id)
        if target_id not in node_map:
            missing_targets.append(target_id)

    if missing_sources or missing_targets:
        print(f"⚠️ 发现边引用了不存在的节点:")
        if missing_sources:
            print(f"  缺失的源节点数: {len(set(missing_sources))}")
            for src in list(set(missing_sources))[:3]:
                print(f"    - {src}")
        if missing_targets:
            print(f"  缺失的目标节点数: {len(set(missing_targets))}")
            for tgt in list(set(missing_targets))[:3]:
                print(f"    - {tgt}")
    else:
        print("✅ 所有边的端点节点都存在")


if __name__ == "__main__":
    asyncio.run(main())
