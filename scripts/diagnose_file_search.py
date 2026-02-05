"""
诊断文件检索问题

问题：用户按部门查询，但看不到文件
可能原因：
1. kb_files 表的 kb_id 格式问题（已修复）
2. 知识库元数据中没有文件信息
3. 文件状态不是 indexed/done

运行：docker compose exec api python scripts/diagnose_file_search.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def diagnose():
    """诊断文件检索问题"""
    logger.info("=" * 70)
    logger.info("诊断文件检索问题")
    logger.info("=" * 70)
    
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 1. 检查研发部的信息
        result = await session.execute(text("""
            SELECT id, name, path
            FROM departments
            WHERE name LIKE '%研发%'
        """))
        dept = result.fetchone()
        
        if not dept:
            logger.error("❌ 找不到研发部！")
            return
        
        dept_id, dept_name, dept_path = dept
        logger.info(f"\n📁 部门信息:")
        logger.info(f"  ID: {dept_id}")
        logger.info(f"  名称: {dept_name}")
        logger.info(f"  路径: {dept_path}")
        
        # 2. 检查该部门关联的知识库
        result = await session.execute(text("""
            SELECT kdr.kb_id, kb.name
            FROM kb_department_relations kdr
            LEFT JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
            WHERE kdr.department_id = :dept_id
        """), {"dept_id": dept_id})
        kb_relations = result.fetchall()
        
        logger.info(f"\n📚 部门关联的知识库 ({len(kb_relations)} 个):")
        for kb_id, kb_name in kb_relations:
            logger.info(f"  - {kb_name} (ID: {kb_id})")
            
            # 检查这个知识库在 kb_files 表中的文件
            result2 = await session.execute(text("""
                SELECT file_id, filename, status, created_at
                FROM kb_files
                WHERE kb_id = :kb_id
                ORDER BY created_at DESC
            """), {"kb_id": kb_id})
            files = result2.fetchall()
            
            logger.info(f"    kb_files 表中的文件: {len(files)} 个")
            for file_id, filename, status, created_at in files[:3]:
                logger.info(f"      - {filename} (status: {status}, created: {created_at})")
        
        # 3. 检查所有 kb_files 表的数据（看是否有孤儿文件）
        result = await session.execute(text("""
            SELECT kf.kb_id, kb.name, COUNT(*) as file_count
            FROM kb_files kf
            LEFT JOIN knowledge_bases kb ON kf.kb_id = kb.db_id
            GROUP BY kf.kb_id, kb.name
            ORDER BY file_count DESC
        """))
        all_kb_files = result.fetchall()
        
        logger.info(f"\n📊 所有知识库的文件统计:")
        for kb_id, kb_name, count in all_kb_files:
            # 检查是否有部门关联
            result2 = await session.execute(text("""
                SELECT department_id
                FROM kb_department_relations
                WHERE kb_id = :kb_id
            """), {"kb_id": kb_id})
            dept_ids = [row[0] for row in result2.fetchall()]
            
            dept_info = f"部门: {dept_ids}" if dept_ids else "⚠️  无部门关联"
            logger.info(f"  - {kb_name or '未知'} ({kb_id}): {count} 个文件, {dept_info}")
        
        # 4. 诊断建议
        logger.info(f"\n" + "=" * 70)
        logger.info("💡 诊断建议:")
        logger.info("=" * 70)
        
        # 检查是否有文件但没有部门关联
        result = await session.execute(text("""
            SELECT DISTINCT kf.kb_id, kb.name
            FROM kb_files kf
            LEFT JOIN knowledge_bases kb ON kf.kb_id = kb.db_id
            LEFT JOIN kb_department_relations kdr ON kf.kb_id = kdr.kb_id
            WHERE kdr.kb_id IS NULL
        """))
        orphan_kbs = result.fetchall()
        
        if orphan_kbs:
            logger.warning(f"\n⚠️  发现 {len(orphan_kbs)} 个知识库有文件但无部门关联:")
            for kb_id, kb_name in orphan_kbs:
                logger.warning(f"  - {kb_name or '未知'} ({kb_id})")
                logger.warning(f"    建议: 在知识库设置中配置部门")
        
        # 检查知识库元数据文件位置
        logger.info(f"\n📂 知识库元数据位置:")
        logger.info(f"  Milvus: saves/knowledge_base_data/milvus_data/metadata_milvus.json")
        logger.info(f"  LightRAG: saves/knowledge_base_data/lightrag_data/metadata_lightrag.json")


async def main():
    try:
        await diagnose()
    except Exception as e:
        logger.error(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
