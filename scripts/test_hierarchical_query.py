"""
测试层级部门查询：父部门能否查到子部门的知识库

测试场景：
- 部门结构: A -> AA -> AAA (AAA是AA的子部门，AA是A的子部门)
- 知识库ZH分配给AAA
- 查询AA部门时，能否查到ZH？

预期结果：应该能查到 ✅
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.services.department_service import DepartmentService
from src.services.user_department_service import UserDepartmentService, KBDepartmentService
from src.knowledge import knowledge_base


async def test_hierarchical_query():
    """测试层级部门查询"""
    
    print("\n" + "="*70)
    print("  测试场景：父部门查询子部门的知识库")
    print("="*70 + "\n")
    
    db = PostgresManager()
    db.initialize()
    dept_service = DepartmentService()
    kb_dept_service = KBDepartmentService()
    
    # 测试数据
    import time
    timestamp = int(time.time())
    
    dept_a_name = f"测试部门A_{timestamp}"
    dept_aa_name = f"测试部门AA_{timestamp}"
    dept_aaa_name = f"测试部门AAA_{timestamp}"
    kb_zh_name = f"测试知识库ZH_{timestamp}"
    
    dept_a_id = None
    dept_aa_id = None
    dept_aaa_id = None
    kb_zh_id = None
    
    try:
        # 1. 创建层级部门
        print("1️⃣  创建层级部门结构")
        
        # 创建 A
        dept_a = await dept_service.create_department(
            name=dept_a_name,
            description="顶层部门A",
            parent_id=None
        )
        dept_a_id = dept_a["id"]
        print(f"   ✅ 部门A: {dept_a_name} (ID: {dept_a_id}, path: {dept_a.get('path')})")
        
        # 创建 AA (A的子部门)
        dept_aa = await dept_service.create_department(
            name=dept_aa_name,
            description="部门AA，A的子部门",
            parent_id=dept_a_id
        )
        dept_aa_id = dept_aa["id"]
        print(f"   ✅ 部门AA: {dept_aa_name} (ID: {dept_aa_id}, path: {dept_aa.get('path')})")
        
        # 创建 AAA (AA的子部门)
        dept_aaa = await dept_service.create_department(
            name=dept_aaa_name,
            description="部门AAA，AA的子部门",
            parent_id=dept_aa_id
        )
        dept_aaa_id = dept_aaa["id"]
        print(f"   ✅ 部门AAA: {dept_aaa_name} (ID: {dept_aaa_id}, path: {dept_aaa.get('path')})")
        
        # 2. 创建知识库ZH，分配给AAA
        print(f"\n2️⃣  创建知识库ZH，分配给部门AAA")
        
        kb_zh = await knowledge_base.create_database(
            database_name=kb_zh_name,
            description="测试知识库，仅分配给AAA",
            kb_type="milvus",
            share_config={
                "is_shared": False,
                "accessible_departments": [dept_aaa_id]
            }
        )
        kb_zh_id = kb_zh["db_id"]
        print(f"   ✅ 知识库ZH: {kb_zh_name} (ID: {kb_zh_id})")
        print(f"   分配给部门: AAA (ID: {dept_aaa_id})")
        
        # 3. 验证数据库中的关联
        print(f"\n3️⃣  验证 kb_department_relations 表")
        
        async with db.get_async_session_context() as session:
            result = await session.execute(
                text("""
                    SELECT kdr.department_id, d.name, d.path
                    FROM kb_department_relations kdr
                    JOIN departments d ON d.id = kdr.department_id
                    WHERE kdr.kb_id = :kb_id
                """),
                {"kb_id": kb_zh_id}
            )
            relations = result.fetchall()
            
            print(f"   知识库 {kb_zh_id[:20]}... 关联的部门:")
            for rel in relations:
                print(f"   - 部门ID: {rel[0]}, 名称: {rel[1]}, 路径: {rel[2]}")
        
        # 4. 测试查询
        print(f"\n4️⃣  测试查询")
        
        # 4.1 查询AAA（直接分配的部门）
        print(f"\n   场景1: 查询部门AAA (ID: {dept_aaa_id})")
        kb_ids_aaa = await kb_dept_service.get_kb_ids_by_departments(
            department_ids=[dept_aaa_id],
            include_subdepts=True
        )
        print(f"   返回的知识库ID: {kb_ids_aaa}")
        if kb_zh_id in kb_ids_aaa:
            print(f"   ✅ 能查到ZH")
        else:
            print(f"   ❌ 查不到ZH")
        
        # 4.2 查询AA（父部门，应该能查到子部门AAA的知识库）
        print(f"\n   场景2: 查询部门AA (ID: {dept_aa_id}) - 关键测试")
        kb_ids_aa = await kb_dept_service.get_kb_ids_by_departments(
            department_ids=[dept_aa_id],
            include_subdepts=True  # 包含子部门
        )
        print(f"   返回的知识库ID: {kb_ids_aa}")
        if kb_zh_id in kb_ids_aa:
            print(f"   ✅ 能查到ZH (正确：父部门能查到子部门的知识库)")
            test_aa_pass = True
        else:
            print(f"   ❌ 查不到ZH (错误：父部门应该能查到子部门的知识库)")
            test_aa_pass = False
        
        # 4.3 查询A（祖父部门，应该能查到所有子孙部门的知识库）
        print(f"\n   场景3: 查询部门A (ID: {dept_a_id})")
        kb_ids_a = await kb_dept_service.get_kb_ids_by_departments(
            department_ids=[dept_a_id],
            include_subdepts=True
        )
        print(f"   返回的知识库ID: {kb_ids_a}")
        if kb_zh_id in kb_ids_a:
            print(f"   ✅ 能查到ZH (正确：祖父部门能查到子孙部门的知识库)")
            test_a_pass = True
        else:
            print(f"   ❌ 查不到ZH (错误：祖父部门应该能查到子孙部门的知识库)")
            test_a_pass = False
        
        # 4.4 不包含子部门的查询
        print(f"\n   场景4: 查询部门AA，但不包含子部门")
        kb_ids_aa_no_sub = await kb_dept_service.get_kb_ids_by_departments(
            department_ids=[dept_aa_id],
            include_subdepts=False  # 不包含子部门
        )
        print(f"   返回的知识库ID: {kb_ids_aa_no_sub}")
        if kb_zh_id in kb_ids_aa_no_sub:
            print(f"   ❌ 查到ZH (错误：不包含子部门时不应该查到)")
        else:
            print(f"   ✅ 查不到ZH (正确：不包含子部门时查不到)")
        
        # 5. 清理测试数据
        print(f"\n5️⃣  清理测试数据")
        
        if kb_zh_id:
            await knowledge_base.delete_database(kb_zh_id)
            print(f"   ✅ 删除知识库 {kb_zh_name}")
        
        if dept_aaa_id:
            await dept_service.delete_department(dept_aaa_id)
            print(f"   ✅ 删除部门 {dept_aaa_name}")
        
        if dept_aa_id:
            await dept_service.delete_department(dept_aa_id)
            print(f"   ✅ 删除部门 {dept_aa_name}")
        
        if dept_a_id:
            await dept_service.delete_department(dept_a_id)
            print(f"   ✅ 删除部门 {dept_a_name}")
        
        # 总结
        print(f"\n{'='*70}")
        if test_aa_pass and test_a_pass:
            print("  ✅ 测试通过：父部门可以查询子部门的知识库")
        else:
            print("  ❌ 测试失败：层级查询存在问题")
            if not test_aa_pass:
                print("     - 父部门AA无法查到子部门AAA的知识库")
            if not test_a_pass:
                print("     - 祖父部门A无法查到子孙部门的知识库")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理（尽力而为）
        try:
            if kb_zh_id:
                await knowledge_base.delete_database(kb_zh_id)
            if dept_aaa_id:
                await dept_service.delete_department(dept_aaa_id)
            if dept_aa_id:
                await dept_service.delete_department(dept_aa_id)
            if dept_a_id:
                await dept_service.delete_department(dept_a_id)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test_hierarchical_query())
