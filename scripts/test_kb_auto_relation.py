"""
测试知识库创建时是否自动创建部门关联
验证修复是否生效
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.knowledge import knowledge_base


async def test_kb_creation_with_departments():
    """测试创建知识库时自动创建部门关联"""
    
    print("\n" + "="*60)
    print("  测试知识库创建时的部门关联")
    print("="*60 + "\n")
    
    db = PostgresManager()
    db.initialize()
    
    # 测试数据
    import time
    timestamp = int(time.time())
    test_kb_name = f"测试自动关联_{timestamp}"
    test_description = "测试知识库创建时自动建立部门关联"
    test_departments = [1, 2, 3]  # 测试部门ID
    
    try:
        # 1. 创建知识库
        print("1️⃣  创建知识库")
        print(f"   名称: {test_kb_name}")
        print(f"   指定部门: {test_departments}")
        
        kb_info = await knowledge_base.create_database(
            database_name=test_kb_name,
            description=test_description,
            kb_type="milvus",
            share_config={
                "is_shared": False,
                "accessible_departments": test_departments
            }
        )
        
        kb_id = kb_info["db_id"]
        print(f"   ✅ 知识库创建成功: {kb_id}")
        
        # 2. 检查 kb_department_relations 表
        print(f"\n2️⃣  检查 kb_department_relations 表")
        
        async with db.get_async_session_context() as session:
            result = await session.execute(
                text("""
                    SELECT department_id 
                    FROM kb_department_relations 
                    WHERE kb_id = :kb_id
                    ORDER BY department_id
                """),
                {"kb_id": kb_id}
            )
            relations = [row.department_id for row in result.fetchall()]
            
            print(f"   关联的部门ID: {relations}")
            
            if relations == test_departments:
                print(f"   ✅ 部门关联自动创建成功！")
                success = True
            else:
                print(f"   ❌ 部门关联不正确")
                print(f"   期望: {test_departments}")
                print(f"   实际: {relations}")
                success = False
        
        # 3. 测试更新知识库部门
        print(f"\n3️⃣  测试更新知识库部门")
        new_departments = [2, 4, 5]
        print(f"   新部门: {new_departments}")
        
        await knowledge_base.update_database(
            db_id=kb_id,
            name=test_kb_name,
            description=test_description,
            share_config={
                "is_shared": False,
                "accessible_departments": new_departments
            }
        )
        
        async with db.get_async_session_context() as session:
            result = await session.execute(
                text("""
                    SELECT department_id 
                    FROM kb_department_relations 
                    WHERE kb_id = :kb_id
                    ORDER BY department_id
                """),
                {"kb_id": kb_id}
            )
            relations = [row.department_id for row in result.fetchall()]
            
            print(f"   更新后的部门ID: {relations}")
            
            if relations == new_departments:
                print(f"   ✅ 部门关联更新成功！")
            else:
                print(f"   ❌ 部门关联更新失败")
                print(f"   期望: {new_departments}")
                print(f"   实际: {relations}")
                success = False
        
        # 4. 清理测试数据
        print(f"\n4️⃣  清理测试数据")
        await knowledge_base.delete_database(kb_id)
        
        # 验证关联也被删除
        async with db.get_async_session_context() as session:
            result = await session.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM kb_department_relations 
                    WHERE kb_id = :kb_id
                """),
                {"kb_id": kb_id}
            )
            count = result.scalar()
            
            if count == 0:
                print(f"   ✅ 关联记录已清理")
            else:
                print(f"   ⚠️  还有 {count} 条关联记录未清理")
        
        print(f"\n{'='*60}")
        if success:
            print("  ✅ 测试通过：部门关联自动创建功能正常")
        else:
            print("  ❌ 测试失败：部门关联功能存在问题")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_kb_creation_with_departments())
