"""
数据库初始化脚本 - 确保数据库结构完整

在全新部署时运行，确保：
1. 所有表已创建
2. 必要的默认值约束已添加
3. 必要的初始数据已插入

运行：docker compose exec api python scripts/init_database.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def init_database():
    """初始化数据库"""
    logger.info("=" * 60)
    logger.info("开始数据库初始化...")
    logger.info("=" * 60)
    
    db = PostgresManager()
    db.initialize()
    
    # 1. 创建所有表
    logger.info("\n📋 步骤 1/3: 创建数据库表...")
    await db.create_tables()
    logger.info("✅ 表结构创建完成")
    
    # 2. 添加必要的默认值约束
    logger.info("\n🔧 步骤 2/3: 添加数据库约束...")
    async with db.get_async_session_context() as session:
        try:
            # departments.is_active 默认值
            await session.execute(text("""
                ALTER TABLE departments 
                ALTER COLUMN is_active SET DEFAULT 1
            """))
            logger.info("   ✅ departments.is_active 默认值")
        except Exception as e:
            if "already" in str(e).lower() or "exists" in str(e).lower():
                logger.info("   ℹ️  departments.is_active 默认值已存在")
            else:
                logger.warning(f"   ⚠️  设置 departments.is_active 默认值失败: {e}")
        
        await session.commit()
    
    logger.info("✅ 数据库约束设置完成")
    
    # 3. 创建默认部门（如果不存在）
    logger.info("\n📁 步骤 3/3: 创建默认部门...")
    async with db.get_async_session_context() as session:
        try:
            # 检查是否存在默认部门
            result = await session.execute(text("""
                SELECT id FROM departments WHERE name = '默认部门'
            """))
            default_dept = result.fetchone()
            
            if not default_dept:
                # 创建默认部门
                result = await session.execute(text("""
                    INSERT INTO departments (name, level, sort_order, description, is_active)
                    VALUES ('默认部门', 1, 0, '系统默认部门', 1)
                    RETURNING id
                """))
                dept_id = result.scalar()
                await session.commit()
                logger.info(f"   ✅ 默认部门创建成功 (ID: {dept_id})")
            else:
                logger.info(f"   ℹ️  默认部门已存在 (ID: {default_dept[0]})")
        except Exception as e:
            logger.error(f"   ❌ 创建默认部门失败: {e}")
            await session.rollback()
    
    # 4. 验证初始化结果
    logger.info("\n✅ 验证初始化结果...")
    async with db.get_async_session_context() as session:
        # 检查表是否存在
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        logger.info(f"   数据库表数量: {len(tables)}")
        
        # 检查 departments 表约束
        result = await session.execute(text("""
            SELECT column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'departments' 
            AND column_name = 'is_active'
        """))
        col_info = result.fetchone()
        
        if col_info:
            has_default = col_info[0] is not None
            is_not_null = col_info[1] == 'NO'
            
            if has_default and is_not_null:
                logger.info("   ✅ departments.is_active 约束正确")
            else:
                logger.warning(f"   ⚠️  departments.is_active 约束不完整: default={col_info[0]}, nullable={col_info[1]}")
        
        # 检查默认部门
        result = await session.execute(text("""
            SELECT COUNT(*) FROM departments
        """))
        dept_count = result.scalar()
        logger.info(f"   部门数量: {dept_count}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 数据库初始化完成！")
    logger.info("=" * 60)
    logger.info("\n现在可以启动应用了：")
    logger.info("   docker compose up -d")
    logger.info("\n或运行批量创建脚本：")
    logger.info("   docker compose exec api python scripts/batch_create_departments_users.py")
    logger.info("=" * 60)


async def main():
    try:
        await init_database()
    except Exception as e:
        logger.error(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
