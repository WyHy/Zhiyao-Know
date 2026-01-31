"""
从 SQLite 迁移数据到 PostgreSQL
"""

import asyncio
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager


async def migrate_data():
    """迁移数据从 SQLite 到 PostgreSQL"""
    sqlite_path = "/app/saves/database/server.db"
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite 数据库不存在: {sqlite_path}")
        return False
    
    print("📦 开始迁移数据...")
    
    # 连接 SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接 PostgreSQL
    db_manager = PostgresManager()
    
    # 需要迁移的表（按依赖顺序）
    tables = [
        "departments",
        "users",
        "conversations",
        "messages",
        "conversation_stats",
        "mcp_servers",
        "tool_calls",
        "operation_logs",
        "message_feedbacks",
    ]
    
    total_migrated = 0
    
    for table in tables:
        try:
            # 获取 SQLite 数据
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  ⏭️  {table}: 0 条记录（跳过）")
                continue
            
            # 获取列名
            columns = [description[0] for description in sqlite_cursor.description]
            
            # 构建插入语句
            placeholders = ", ".join([f":{col}" for col in columns])
            cols = ", ".join(columns)
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            
            # 插入数据到 PostgreSQL
            async with db_manager.get_session() as session:
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    await session.execute(text(insert_sql), row_dict)
                await session.commit()
            
            print(f"  ✅ {table}: 迁移了 {len(rows)} 条记录")
            total_migrated += len(rows)
            
        except Exception as e:
            print(f"  ❌ {table}: 迁移失败 - {e}")
    
    sqlite_conn.close()
    
    print(f"\n🎉 迁移完成！总共迁移了 {total_migrated} 条记录")
    return True


if __name__ == "__main__":
    success = asyncio.run(migrate_data())
    sys.exit(0 if success else 1)
