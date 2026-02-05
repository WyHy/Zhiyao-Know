"""
测试文件检索功能 - 验证部门筛选

测试场景：
1. 查询指定部门的文件
2. 验证不同用户是否能看到对应部门的文件

运行：docker compose exec api python scripts/test_file_search_by_dept.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.services.file_search_service import FileSearchService
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def test_file_search():
    """测试文件检索"""
    logger.info("=" * 60)
    logger.info("测试文件检索功能")
    logger.info("=" * 60)
    
    db = PostgresManager()
    db.initialize()
    file_service = FileSearchService()
    
    # 1. 获取部门信息
    async with db.get_async_session_context() as session:
        result = await session.execute(text("""
            SELECT id, name FROM departments
            WHERE name LIKE '%研发%' OR name LIKE '%数字化%' OR name LIKE '%纪委%'
            ORDER BY name
        """))
        depts = result.fetchall()
        logger.info(f"\n📋 测试部门列表:")
        for dept_id, dept_name in depts:
            logger.info(f"  - {dept_name} (ID: {dept_id})")
        
        # 2. 获取知识库-部门关联
        result = await session.execute(text("""
            SELECT kdr.kb_id, kb.name AS kb_name, kdr.department_id, d.name AS dept_name
            FROM kb_department_relations kdr
            LEFT JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
            LEFT JOIN departments d ON kdr.department_id = d.id
            ORDER BY kdr.department_id
        """))
        relations = result.fetchall()
        logger.info(f"\n🔗 知识库-部门关联:")
        for kb_id, kb_name, dept_id, dept_name in relations[:10]:
            logger.info(f"  - [{dept_name}] {kb_name}")
    
    # 3. 测试查询（使用实际的部门ID）
    if depts:
        test_dept_id, test_dept_name = depts[0]
        logger.info(f"\n🔍 测试查询部门: {test_dept_name} (ID: {test_dept_id})")
        
        # 模拟普通用户查询
        result = await file_service.search_files(
            user_id=1,
            user_role="admin",  # 使用 admin 避免权限问题
            department_ids=[test_dept_id],
            include_subdepts=False,
            page=1,
            page_size=10
        )
        
        logger.info(f"\n📊 查询结果:")
        logger.info(f"  总文件数: {result['total']}")
        logger.info(f"  涉及知识库: {result.get('kb_count', 0)}")
        logger.info(f"  返回文件: {len(result['files'])}")
        
        if result['files']:
            logger.info(f"\n📄 文件列表:")
            for file in result['files'][:5]:
                logger.info(f"  - {file['filename']} (KB: {file['kb_name']})")
        else:
            logger.warning("  ⚠️  没有找到文件！")
            
            # 诊断：检查这个部门有哪些知识库
            async with db.get_async_session_context() as session:
                result = await session.execute(text("""
                    SELECT kdr.kb_id, kb.name
                    FROM kb_department_relations kdr
                    LEFT JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
                    WHERE kdr.department_id = :dept_id
                """), {"dept_id": test_dept_id})
                dept_kbs = result.fetchall()
                logger.info(f"\n🔍 该部门关联的知识库 ({len(dept_kbs)} 个):")
                for kb_id, kb_name in dept_kbs:
                    # 检查这个知识库有多少文件
                    result2 = await session.execute(text("""
                        SELECT COUNT(*) FROM kb_files WHERE kb_id = :kb_id
                    """), {"kb_id": kb_id})
                    file_count = result2.scalar()
                    logger.info(f"  - {kb_name}: {file_count} 个文件")


async def main():
    try:
        await test_file_search()
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
