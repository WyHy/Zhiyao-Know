"""
诊断知识库数据结构 - 对比本地和生产环境
找出文件检索为空的原因
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.knowledge import knowledge_base


async def diagnose_environment(env_name: str = "当前环境"):
    """诊断当前环境的知识库数据"""
    
    print(f"\n{'='*60}")
    print(f"  {env_name} - 知识库数据诊断")
    print(f"{'='*60}\n")
    
    db = PostgresManager()
    db.initialize()  # 移除 await，PostgresManager.initialize() 是同步的
    
    try:
        async with db.get_async_session_context() as session:
            # 1. 检查 knowledge_bases 表
            print("📊 1. 检查 knowledge_bases 表")
            result = await session.execute(
                text("SELECT COUNT(*) as total FROM knowledge_bases")
            )
            kb_count = result.scalar()
            print(f"   知识库总数: {kb_count}")
            
            if kb_count > 0:
                result = await session.execute(
                    text("""
                        SELECT db_id, name, kb_type, share_config 
                        FROM knowledge_bases 
                        LIMIT 5
                    """)
                )
                kbs = result.fetchall()
                print(f"\n   前5个知识库:")
                for kb in kbs:
                    print(f"   - ID: {kb.db_id}")
                    print(f"     名称: {kb.name}")
                    print(f"     类型: {kb.kb_type}")
                    print(f"     共享配置: {kb.share_config}")
                    print()
            
            # 2. 检查 kb_department_relations 表
            print("\n📊 2. 检查 kb_department_relations 表")
            result = await session.execute(
                text("SELECT COUNT(*) as total FROM kb_department_relations")
            )
            relation_count = result.scalar()
            print(f"   知识库-部门关系总数: {relation_count}")
            
            if relation_count > 0:
                result = await session.execute(
                    text("""
                        SELECT kdr.kb_id, kdr.department_id, d.name as dept_name
                        FROM kb_department_relations kdr
                        LEFT JOIN departments d ON d.id = kdr.department_id
                        LIMIT 10
                    """)
                )
                relations = result.fetchall()
                print(f"\n   前10条关系:")
                for rel in relations:
                    print(f"   - KB_ID: {rel.kb_id}, 部门ID: {rel.department_id}, 部门名: {rel.dept_name}")
            
            # 3. 检查 departments 表
            print("\n\n📊 3. 检查 departments 表")
            result = await session.execute(
                text("SELECT COUNT(*) as total FROM departments")
            )
            dept_count = result.scalar()
            print(f"   部门总数: {dept_count}")
            
            if dept_count > 0:
                result = await session.execute(
                    text("""
                        SELECT id, name, parent_id, 
                               (SELECT COUNT(*) FROM user_department_relations WHERE department_id = departments.id) as user_count
                        FROM departments
                        ORDER BY id
                        LIMIT 10
                    """)
                )
                depts = result.fetchall()
                print(f"\n   前10个部门:")
                for dept in depts:
                    print(f"   - ID: {dept.id}, 名称: {dept.name}, 父部门: {dept.parent_id}, 用户数: {dept.user_count}")
            
            # 4. 检查 kb_id 数据类型一致性
            print("\n\n📊 4. 检查 kb_id 数据类型一致性")
            result = await session.execute(
                text("""
                    SELECT 
                        kb.db_id,
                        pg_typeof(kb.db_id) as kb_type,
                        kdr.kb_id,
                        pg_typeof(kdr.kb_id) as relation_type
                    FROM knowledge_bases kb
                    LEFT JOIN kb_department_relations kdr ON kb.db_id = kdr.kb_id
                    LIMIT 5
                """)
            )
            type_checks = result.fetchall()
            print(f"\n   数据类型检查:")
            for check in type_checks:
                print(f"   - knowledge_bases.db_id: {check.db_id} (类型: {check.kb_type})")
                print(f"     kb_department_relations.kb_id: {check.kb_id} (类型: {check.relation_type})")
                print()
            
            # 5. 检查知识库文件元数据（从 knowledge_base manager）
            print("\n📊 5. 检查知识库文件元数据")
            try:
                all_dbs = await knowledge_base.get_databases()
                kb_list = all_dbs.get("databases", [])
                print(f"   knowledge_base.get_databases() 返回: {len(kb_list)} 个知识库")
                
                if kb_list:
                    # 检查第一个知识库的文件
                    first_kb = kb_list[0]
                    kb_id = first_kb.get("db_id")
                    print(f"\n   检查知识库: {first_kb.get('name')} (ID: {kb_id})")
                    
                    try:
                        kb_info = await knowledge_base.get_database_info(kb_id)
                        files = kb_info.get("files", [])
                        print(f"   文件数量: {len(files)}")
                        
                        if files:
                            print(f"\n   前3个文件:")
                            for i, f in enumerate(files[:3], 1):
                                print(f"   {i}. {f.get('filename', 'N/A')}")
                                print(f"      类型: {f.get('file_type', 'N/A')}")
                                print(f"      大小: {f.get('file_size', 0)} bytes")
                    except Exception as e:
                        print(f"   ⚠️  获取文件列表失败: {e}")
                        
            except Exception as e:
                print(f"   ⚠️  获取知识库列表失败: {e}")
            
            # 6. 检查 kb_department_relations 中的 kb_id 是否都能在 knowledge_bases 中找到
            print("\n\n📊 6. 检查关系完整性")
            result = await session.execute(
                text("""
                    SELECT COUNT(*) as orphan_count
                    FROM kb_department_relations kdr
                    LEFT JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
                    WHERE kb.id IS NULL
                """)
            )
            orphan_count = result.scalar()
            print(f"   孤立的关系记录（kb_id 在 knowledge_bases 中不存在）: {orphan_count}")
            
            if orphan_count > 0:
                print("   ⚠️  警告：存在孤立的关系记录！")
                result = await session.execute(
                    text("""
                        SELECT kdr.kb_id, kdr.department_id
                        FROM kb_department_relations kdr
                        LEFT JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
                        WHERE kb.id IS NULL
                        LIMIT 10
                    """)
                )
                orphans = result.fetchall()
                for orphan in orphans:
                    print(f"   - KB_ID: {orphan.kb_id}, 部门ID: {orphan.department_id}")
            
            # 7. 模拟文件检索查询
            print("\n\n📊 7. 模拟文件检索流程")
            
            # 获取第一个部门
            result = await session.execute(
                text("SELECT id, name FROM departments ORDER BY id LIMIT 1")
            )
            first_dept = result.fetchone()
            
            if first_dept:
                dept_id = first_dept.id
                dept_name = first_dept.name
                print(f"   使用部门: {dept_name} (ID: {dept_id})")
                
                # 查询该部门关联的知识库
                result = await session.execute(
                    text("""
                        SELECT kb_id FROM kb_department_relations
                        WHERE department_id = :dept_id
                    """),
                    {"dept_id": dept_id}
                )
                kb_ids = [row.kb_id for row in result.fetchall()]
                print(f"   该部门关联的知识库ID: {kb_ids}")
                
                if kb_ids:
                    # 检查这些知识库是否有文件
                    for kb_id in kb_ids[:3]:  # 最多检查3个
                        try:
                            kb_info = await knowledge_base.get_database_info(kb_id)
                            files = kb_info.get("files", [])
                            print(f"   - KB {kb_id}: {len(files)} 个文件")
                        except Exception as e:
                            print(f"   - KB {kb_id}: ⚠️  无法获取 ({e})")
                else:
                    print(f"   ⚠️  该部门没有关联任何知识库！")
            
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}\n")


async def compare_with_production(prod_host: str, prod_user: str, prod_password: str):
    """对比生产环境（需要提供生产环境数据库连接信息）"""
    print("\n⚠️  对比生产环境需要配置生产数据库连接")
    print("暂时仅诊断当前环境，如需对比请手动在生产服务器上运行此脚本")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("  知识库数据结构诊断工具")
    print("="*60)
    
    # 诊断当前环境
    await diagnose_environment("当前环境")
    
    print("\n💡 建议:")
    print("   1. 在生产服务器上运行相同的脚本:")
    print("      docker compose exec api python scripts/diagnose_kb_data.py")
    print()
    print("   2. 对比两个环境的输出，重点检查:")
    print("      - kb_department_relations 表的记录数")
    print("      - kb_id 的数据类型是否一致")
    print("      - 知识库文件元数据是否存在")
    print("      - 部门与知识库的关联关系是否正确")
    print()
    print("   3. 如果生产环境缺少 kb_department_relations，运行迁移脚本:")
    print("      docker compose exec api python scripts/migrate_kb_department_relations.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
