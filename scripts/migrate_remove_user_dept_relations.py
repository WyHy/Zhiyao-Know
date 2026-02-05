#!/usr/bin/env python3
"""
数据库迁移脚本：删除 user_department_relations 表

该脚本执行以下操作：
1. 将 user_department_relations 表中 is_primary=1 的记录同步到 users.department_id
2. 删除 user_department_relations 表

运行方式：
    docker compose exec api uv run python scripts/migrate_remove_user_dept_relations.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager


async def migrate():
    """执行迁移"""
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 检查表是否存在
        check_table = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_department_relations'
                )
            """)
        )
        table_exists = check_table.fetchone()[0]
        
        if not table_exists:
            print("✅ user_department_relations 表不存在，无需迁移")
            return
        
        print("开始迁移 user_department_relations 数据...")
        
        # 1. 统计现有数据
        count_result = await session.execute(
            text("SELECT COUNT(*) FROM user_department_relations")
        )
        total_count = count_result.fetchone()[0]
        print(f"   - 总记录数: {total_count}")
        
        primary_count_result = await session.execute(
            text("SELECT COUNT(*) FROM user_department_relations WHERE is_primary = 1")
        )
        primary_count = primary_count_result.fetchone()[0]
        print(f"   - 主部门记录数: {primary_count}")
        
        # 2. 将主部门同步到 users.department_id
        print("\n同步主部门到 users.department_id...")
        update_result = await session.execute(
            text("""
                UPDATE users u
                SET department_id = udr.department_id
                FROM user_department_relations udr
                WHERE u.id = udr.user_id 
                  AND udr.is_primary = 1
                  AND (u.department_id IS NULL OR u.department_id != udr.department_id)
            """)
        )
        updated_count = update_result.rowcount
        print(f"   - 更新了 {updated_count} 个用户的 department_id")
        
        # 3. 删除 user_department_relations 表
        print("\n删除 user_department_relations 表...")
        await session.execute(text("DROP TABLE IF EXISTS user_department_relations CASCADE"))
        print("   ✅ 表已删除")
        
        await session.commit()
        print("\n✅ 迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
