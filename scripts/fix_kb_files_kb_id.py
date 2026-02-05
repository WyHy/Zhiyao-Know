"""
修复 kb_files 表的 kb_id 格式问题

问题：kb_files 表中存储的是数字格式的 kb_id (如 "3", "4")
     但应该存储字符串格式 (如 "kb_xxx")
     
解决：
1. 创建 id -> db_id 的映射（从旧的 knowledge_databases 表或其他来源）
2. 更新 kb_files 表中的 kb_id

运行：docker compose exec api python scripts/fix_kb_files_kb_id.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def fix_kb_files_kb_id():
    """修复 kb_files 表的 kb_id 格式"""
    logger.info("=" * 60)
    logger.info("开始修复 kb_files 表的 kb_id 格式...")
    logger.info("=" * 60)
    
    db = PostgresManager()
    db.initialize()
    
    # 1. 获取 knowledge_bases 表的映射
    async with db.get_async_session_context() as session:
        logger.info("尝试从现有数据推断映射...")
        # 按创建时间排序获取所有知识库
        result = await session.execute(text("""
            SELECT db_id
            FROM knowledge_bases
            ORDER BY created_at ASC
        """))
        kb_list = [row[0] for row in result.fetchall()]
        
        # 创建映射：1->第一个db_id, 2->第二个db_id, ...
        old_mapping = {str(i+1): db_id for i, db_id in enumerate(kb_list)}
        logger.info(f"推断映射 ({len(old_mapping)} 条):")
        for k, v in list(old_mapping.items())[:5]:
            logger.info(f"  {k} -> {v}")
    
    # 2. 检查需要修复的记录
    async with db.get_async_session_context() as session:
        result = await session.execute(text("""
            SELECT DISTINCT kb_id
            FROM kb_files
            WHERE kb_id NOT LIKE 'kb_%'
            ORDER BY kb_id
        """))
        numeric_kb_ids = [row[0] for row in result.fetchall()]
        
        if not numeric_kb_ids:
            logger.info("✅ 没有需要修复的记录")
            return
        
        logger.info(f"\n📋 发现 {len(numeric_kb_ids)} 个数字格式的 kb_id: {numeric_kb_ids}")
        
        # 4. 逐个更新
        updated_count = 0
        for numeric_id in numeric_kb_ids:
            if numeric_id in old_mapping:
                new_kb_id = old_mapping[numeric_id]
                
                # 更新记录
                result = await session.execute(text("""
                    UPDATE kb_files
                    SET kb_id = :new_kb_id
                    WHERE kb_id = :old_kb_id
                """), {"new_kb_id": new_kb_id, "old_kb_id": numeric_id})
                
                count = result.rowcount
                updated_count += count
                logger.info(f"  ✅ 更新 kb_id: {numeric_id} -> {new_kb_id} ({count} 条记录)")
            else:
                logger.warning(f"  ⚠️  无法找到数字 ID {numeric_id} 对应的 db_id，跳过")
        
        await session.commit()
        logger.info(f"\n✅ 修复完成！共更新 {updated_count} 条记录")
        
        # 5. 验证结果
        result = await session.execute(text("""
            SELECT COUNT(*) 
            FROM kb_files
            WHERE kb_id NOT LIKE 'kb_%'
        """))
        remaining = result.scalar()
        
        if remaining > 0:
            logger.warning(f"⚠️  仍有 {remaining} 条记录未修复")
        else:
            logger.info("✅ 所有记录已修复！")
        
        # 显示修复后的数据
        result = await session.execute(text("""
            SELECT DISTINCT kb_id
            FROM kb_files
            ORDER BY kb_id
            LIMIT 10
        """))
        kb_ids = [row[0] for row in result.fetchall()]
        logger.info(f"\n修复后的 kb_id 列表: {kb_ids}")


async def main():
    try:
        await fix_kb_files_kb_id()
    except Exception as e:
        logger.error(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
