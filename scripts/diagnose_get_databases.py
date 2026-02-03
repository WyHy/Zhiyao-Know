"""
快速诊断：为什么 get_databases() 返回空
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge import knowledge_base


async def diagnose_get_databases():
    print("\n=== 诊断 knowledge_base.get_databases() ===\n")
    
    try:
        # 1. 直接调用 get_databases()
        print("1️⃣  调用 knowledge_base.get_databases()")
        result = await knowledge_base.get_databases()
        
        print(f"   返回类型: {type(result)}")
        print(f"   返回内容: {result}")
        print(f"   databases 数量: {len(result.get('databases', []))}")
        
        # 2. 检查内部状态
        print("\n2️⃣  检查 knowledge_base 内部状态")
        print(f"   work_dir: {knowledge_base.work_dir}")
        print(f"   adapter 类型: {type(knowledge_base.adapter).__name__}")
        
        # 3. 尝试访问底层数据
        if hasattr(knowledge_base.adapter, '_databases'):
            print(f"   adapter._databases: {knowledge_base.adapter._databases}")
        
        # 4. 尝试直接从数据库获取
        print("\n3️⃣  尝试直接查询数据库")
        from src.storage.postgres.manager import PostgresManager
        from sqlalchemy import text
        
        db = PostgresManager()
        db.initialize()
        
        async with db.get_async_session_context() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM knowledge_bases")
            )
            count = result.scalar()
            print(f"   knowledge_bases 表记录数: {count}")
            
            if count > 0:
                result = await session.execute(
                    text("SELECT db_id, name, kb_type FROM knowledge_bases LIMIT 5")
                )
                kbs = result.fetchall()
                print(f"\n   前5个知识库:")
                for kb in kbs:
                    print(f"   - {kb.db_id}: {kb.name} ({kb.kb_type})")
        
        # 5. 测试 get_databases_by_user
        print("\n4️⃣  测试 get_databases_by_user")
        user_info = {
            "role": "superadmin",
            "user_id": 1,
            "department_id": None
        }
        result = await knowledge_base.get_databases_by_user(user_info)
        print(f"   superadmin 可见的知识库数: {len(result.get('databases', []))}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose_get_databases())
