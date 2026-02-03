#!/usr/bin/env python3
"""
修复部门表的唯一索引：从全局唯一改为同父部门下唯一
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def fix_department_unique_constraint():
    """修复部门表的唯一约束"""
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        logger.info("开始修复部门表唯一约束...")
        
        try:
            # 1. 检查旧索引是否存在
            old_index_check = await session.execute(
                text("""
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'departments' AND indexname = 'ix_departments_name'
                """)
            )
            old_index_exists = old_index_check.fetchone() is not None
            
            if old_index_exists:
                logger.info("1. 删除旧的全局唯一索引 ix_departments_name...")
                await session.execute(
                    text("DROP INDEX IF EXISTS ix_departments_name")
                )
                await session.commit()
                logger.info("   ✅ 已删除")
            else:
                logger.info("1. 旧索引 ix_departments_name 不存在，跳过删除")
            
            # 2. 检查新索引是否存在
            new_index_check = await session.execute(
                text("""
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'departments' AND indexname = 'ix_departments_name_parent'
                """)
            )
            new_index_exists = new_index_check.fetchone() is not None
            
            if new_index_exists:
                logger.info("2. 联合唯一索引 ix_departments_name_parent 已存在，跳过创建")
            else:
                logger.info("2. 创建新的联合唯一约束（同父部门下不允许同名）...")
                await session.execute(
                    text("""
                        CREATE UNIQUE INDEX ix_departments_name_parent 
                        ON departments (name, COALESCE(parent_id, 0))
                    """)
                )
                await session.commit()
                logger.info("   ✅ 已创建")
            
            logger.info("✅ 部门表唯一约束修复完成！")
            logger.info("   现在允许不同父部门下有同名子部门，但同一父部门下不允许重名")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ 修复失败: {e}")
            raise


async def main():
    try:
        await fix_department_unique_constraint()
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
