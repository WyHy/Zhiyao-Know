"""
清空所有知识库的脚本

警告：此操作不可逆，会删除所有知识库数据！

运行方式：
    docker compose exec api uv run python scripts/clear_all_knowledge_bases.py
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.config.app import config
from src.storage.postgres.manager import PostgresManager


async def clear_database_tables(session) -> dict:
    """清理数据库表"""
    stats = {}
    
    # 按依赖顺序清理关联表
    tables = [
        ("kb_files", "DELETE FROM kb_files"),  # 可能已删除，忽略错误
        ("knowledge_files", "DELETE FROM knowledge_files"),
        ("kb_department_relations", "DELETE FROM kb_department_relations"),
        ("kb_access_control", "DELETE FROM kb_access_control"),
        ("knowledge_bases", "DELETE FROM knowledge_bases"),
    ]
    
    for table_name, sql in tables:
        try:
            result = await session.execute(text(sql))
            stats[table_name] = result.rowcount
            print(f"   ✅ 清理 {table_name}: {result.rowcount} 条记录")
        except Exception as e:
            # 表可能不存在，忽略
            stats[table_name] = 0
            print(f"   ⚠️  跳过 {table_name}: {e}")
    
    return stats


def clear_file_storage() -> int:
    """清理文件存储"""
    kb_data_dir = os.path.join(config.save_dir, "knowledge_base_data")
    
    if not os.path.exists(kb_data_dir):
        print(f"   ⚠️  目录不存在: {kb_data_dir}")
        return 0
    
    # 统计文件数
    file_count = sum(len(files) for _, _, files in os.walk(kb_data_dir))
    
    # 删除目录内容
    for item in os.listdir(kb_data_dir):
        item_path = os.path.join(kb_data_dir, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"   ⚠️  删除失败 {item_path}: {e}")
    
    print(f"   ✅ 清理文件存储: {file_count} 个文件")
    return file_count


async def clear_milvus_collections() -> int:
    """清理 Milvus 向量数据库"""
    try:
        from pymilvus import connections, utility
        
        milvus_uri = os.getenv("MILVUS_URI", "http://milvus:19530")
        milvus_db = os.getenv("MILVUS_DB_NAME", "default")
        
        # 连接 Milvus
        connections.connect(alias="clear_script", uri=milvus_uri, db_name=milvus_db)
        
        # 获取所有 collection
        collections = utility.list_collections(using="clear_script")
        
        # 删除所有 collection
        deleted = 0
        for coll_name in collections:
            try:
                utility.drop_collection(coll_name, using="clear_script")
                deleted += 1
                print(f"   ✅ 删除 Milvus collection: {coll_name}")
            except Exception as e:
                print(f"   ⚠️  删除失败 {coll_name}: {e}")
        
        connections.disconnect("clear_script")
        return deleted
        
    except ImportError:
        print("   ⚠️  pymilvus 未安装，跳过 Milvus 清理")
        return 0
    except Exception as e:
        print(f"   ⚠️  Milvus 连接失败: {e}")
        return 0


async def clear_all_knowledge_bases():
    """清空所有知识库"""
    
    print("=" * 60)
    print("⚠️  警告：此操作将删除所有知识库数据！")
    print("=" * 60)
    
    # 初始化数据库
    db = PostgresManager()
    db.initialize()
    
    try:
        async with db.get_async_session_context() as session:
            # 1. 获取所有知识库
            result = await session.execute(text("SELECT db_id, name, kb_type FROM knowledge_bases"))
            kbs = result.fetchall()
            
            print(f"\n📚 找到 {len(kbs)} 个知识库:")
            for db_id, name, kb_type in kbs:
                print(f"  - {name} ({db_id}) [{kb_type}]")
            
            # 2. 清理数据库表
            print("\n🧹 清理数据库表...")
            await clear_database_tables(session)
            await session.commit()
            
            # 3. 清理文件存储
            print("\n🧹 清理文件存储...")
            clear_file_storage()
            
            # 4. 清理 Milvus 向量数据库
            print("\n🧹 清理 Milvus 向量数据库...")
            await clear_milvus_collections()
            
            print("\n" + "=" * 60)
            print("✅ 所有知识库数据已清空！")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ 清空失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(clear_all_knowledge_bases())
