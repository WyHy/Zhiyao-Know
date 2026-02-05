#!/usr/bin/env python3
"""
数据库迁移脚本：删除 kb_files 表

背景：
- kb_files 表原本用于文件检索优化
- 现在文件检索直接使用 knowledge_files 表
- kb_files 表不再需要

运行方式：
    docker compose exec api uv run python scripts/migrate_remove_kb_files_table.py
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
                    WHERE table_name = 'kb_files'
                )
            """)
        )
        table_exists = check_table.fetchone()[0]
        
        if not table_exists:
            print("✅ kb_files 表不存在，无需迁移")
            return
        
        # 统计现有数据
        count_result = await session.execute(
            text("SELECT COUNT(*) FROM kb_files")
        )
        total_count = count_result.fetchone()[0]
        print(f"kb_files 表中有 {total_count} 条记录")
        
        if total_count > 0:
            print("\n注意：kb_files 表中的数据将被删除。")
            print("文件检索现在使用 knowledge_files 表，不会丢失数据。")
        
        # 删除 kb_files 表
        print("\n删除 kb_files 表...")
        await session.execute(text("DROP TABLE IF EXISTS kb_files CASCADE"))
        await session.commit()
        print("✅ kb_files 表已删除")
        
        print("\n✅ 迁移完成！文件检索现在使用 knowledge_files 表。")


if __name__ == "__main__":
    asyncio.run(migrate())
