"""
快速检查清单 - 对比本地和生产环境
用于排查文件检索为空的问题
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager


async def quick_check():
    """快速检查数据库关键信息"""
    
    print("\n" + "="*60)
    print("  快速检查清单 - 数据库关键信息")
    print("="*60 + "\n")
    
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 1. 知识库数量
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_bases"))
        kb_count = result.scalar()
        print(f"✓ 知识库总数: {kb_count}")
        
        # 2. 部门关系数量
        result = await session.execute(text("SELECT COUNT(*) FROM kb_department_relations"))
        relation_count = result.scalar()
        print(f"✓ 知识库-部门关系数: {relation_count}")
        
        # 3. 部门数量
        result = await session.execute(text("SELECT COUNT(*) FROM departments"))
        dept_count = result.scalar()
        print(f"✓ 部门总数: {dept_count}")
        
        # 4. 检查是否有知识库没有部门关联
        result = await session.execute(text("""
            SELECT COUNT(*) 
            FROM knowledge_bases kb
            LEFT JOIN kb_department_relations kdr ON kb.db_id = kdr.kb_id
            WHERE kdr.kb_id IS NULL
        """))
        unlinked_kb_count = result.scalar()
        print(f"{'⚠️ ' if unlinked_kb_count > 0 else '✓ '} 没有部门关联的知识库: {unlinked_kb_count}")
        
        # 5. 示例：查看知识库和部门关联
        if kb_count > 0 and relation_count > 0:
            print("\n📋 知识库-部门关联示例（前5条）:")
            result = await session.execute(text("""
                SELECT 
                    kb.name as kb_name,
                    kb.db_id,
                    d.name as dept_name,
                    d.id as dept_id
                FROM kb_department_relations kdr
                JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
                JOIN departments d ON kdr.department_id = d.id
                LIMIT 5
            """))
            rows = result.fetchall()
            for row in rows:
                print(f"   - {row.kb_name} ({row.db_id[:20]}...) → {row.dept_name} (ID:{row.dept_id})")
        
        # 6. 检查知识库共享配置
        print("\n📋 知识库共享配置:")
        result = await session.execute(text("""
            SELECT name, share_config
            FROM knowledge_bases
            LIMIT 5
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"   - {row.name}: {row.share_config}")
        
        # 7. 测试一个具体的检索场景
        print("\n🔍 测试检索场景:")
        # 获取第一个有关联的部门
        result = await session.execute(text("""
            SELECT DISTINCT d.id, d.name
            FROM departments d
            JOIN kb_department_relations kdr ON kdr.department_id = d.id
            LIMIT 1
        """))
        dept = result.fetchone()
        
        if dept:
            print(f"   测试部门: {dept.name} (ID: {dept.id})")
            
            # 查询该部门的知识库
            result = await session.execute(text("""
                SELECT kb.db_id, kb.name
                FROM kb_department_relations kdr
                JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
                WHERE kdr.department_id = :dept_id
            """), {"dept_id": dept.id})
            kbs = result.fetchall()
            
            print(f"   该部门关联的知识库: {len(kbs)} 个")
            for kb in kbs:
                print(f"     - {kb.name} ({kb.db_id})")
        else:
            print("   ⚠️  没有部门有知识库关联")
    
    print("\n" + "="*60)
    print("  检查完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(quick_check())
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
