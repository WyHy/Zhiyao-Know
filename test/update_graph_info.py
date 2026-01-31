"""
手动触发图谱信息更新
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge.services.upload_graph_service import UploadGraphService

def main():
    print("=== 更新图谱信息 ===\n")
    
    service = UploadGraphService()
    
    # 获取最新的图谱信息
    info = service.get_graph_info("neo4j")
    
    print(f"实体数量: {info.get('entity_count')}")
    print(f"关系数量: {info.get('relationship_count')}")
    print(f"缺少 embedding 的节点数: {info.get('nodes_without_embedding', 0)}")
    
    # 保存到文件
    success = service.save_graph_info("neo4j")
    
    if success:
        print("\n✅ 图谱信息已更新并保存")
    else:
        print("\n❌ 保存失败")

if __name__ == "__main__":
    main()
