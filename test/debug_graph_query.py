"""
调试图谱查询问题
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge.adapters.upload import UploadGraphAdapter


async def main():
    print("=== 测试 Upload 图谱查询 ===\n")

    # 初始化适配器
    adapter = UploadGraphAdapter()

    # 测试查询
    print("1. 查询所有节点（node_label='*', max_nodes=50）")
    result = await adapter.query_nodes(keyword="*", max_nodes=50)

    print(f"\n返回结果:")
    print(f"  节点数: {len(result.get('nodes', []))}")
    print(f"  边数: {len(result.get('edges', []))}")

    if result.get("nodes"):
        print(f"\n前1个节点（标准化后）:")
        node = result["nodes"][0]
        print(f"  ID: {node.get('id')}")
        print(f"  Name: {node.get('name')}")
        print(f"  Labels: {node.get('labels')}")
        print(f"  所有键: {list(node.keys())[:10]}")

    if result.get("edges"):
        print(f"\n前1条边（标准化后）:")
        edge = result["edges"][0]
        print(f"  ID: {edge.get('id')}")
        print(f"  Type: {edge.get('type')}")
        print(f"  Source ID: {edge.get('source_id')}")
        print(f"  Target ID: {edge.get('target_id')}")
        print(f"  所有键: {list(edge.keys())}")

    # 测试 BaseNeo4jAdapter 的直接查询
    print("\n\n2. 直接测试 BaseNeo4jAdapter._get_sample_nodes_with_connections")
    raw_result = adapter._db._get_sample_nodes_with_connections(num=50, label_filter="Upload")

    print(f"\n原始返回结果:")
    print(f"  节点数: {len(raw_result.get('nodes', []))}")
    print(f"  边数: {len(raw_result.get('edges', []))}")

    if raw_result.get("nodes"):
        print(f"\n第1个节点的完整数据结构:")
        import json

        print(json.dumps(raw_result["nodes"][0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
