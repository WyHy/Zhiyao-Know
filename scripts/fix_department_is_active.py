"""
修复 departments 表的 is_active 字段问题

问题：
- is_active 字段在代码中定义为 nullable=False, default=1
- 但数据库中没有 DEFAULT 约束
- 导致使用原生 SQL 插入时报错 "null value violates not-null constraint"

解决方案：
1. 为现有数据设置默认值（如果有 NULL）
2. 添加 DEFAULT 约束
3. 确保非空约束生效

运行：docker compose exec api python scripts/fix_department_is_active.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager


async def fix_department_is_active():
    """修复 departments 表的 is_active 字段"""
    db = PostgresManager()
    db.initialize()
    
    print("🔧 开始修复 departments.is_active 字段")
    print("=" * 60)
    
    async with db.get_async_session_context() as session:
        try:
            # 1. 检查当前状态
            print("\n📊 检查当前状态...")
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(is_active) as non_null,
                    COUNT(*) - COUNT(is_active) as null_count
                FROM departments
            """))
            stats = result.fetchone()
            print(f"   总部门数: {stats[0]}")
            print(f"   非空数量: {stats[1]}")
            print(f"   NULL数量: {stats[2]}")
            
            # 2. 更新所有 NULL 值为 1
            if stats[2] > 0:
                print(f"\n🔄 更新 {stats[2]} 个 NULL 值为 1...")
                await session.execute(text("""
                    UPDATE departments 
                    SET is_active = 1 
                    WHERE is_active IS NULL
                """))
                print("   ✅ NULL 值已更新")
            else:
                print("\n✅ 没有 NULL 值，跳过更新")
            
            # 3. 设置默认值约束（如果不存在）
            print("\n🔧 设置字段默认值...")
            try:
                await session.execute(text("""
                    ALTER TABLE departments 
                    ALTER COLUMN is_active SET DEFAULT 1
                """))
                print("   ✅ 默认值已设置为 1")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("   ℹ️  默认值约束已存在")
                else:
                    raise
            
            # 4. 确保非空约束（如果不存在）
            print("\n🔒 确保非空约束...")
            try:
                await session.execute(text("""
                    ALTER TABLE departments 
                    ALTER COLUMN is_active SET NOT NULL
                """))
                print("   ✅ 非空约束已设置")
            except Exception as e:
                if "already" in str(e).lower():
                    print("   ℹ️  非空约束已存在")
                else:
                    raise
            
            await session.commit()
            
            # 5. 验证修复结果
            print("\n✅ 验证修复结果...")
            result = await session.execute(text("""
                SELECT column_name, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'departments' 
                AND column_name = 'is_active'
            """))
            col_info = result.fetchone()
            
            print(f"   字段名: {col_info[0]}")
            print(f"   可为空: {col_info[1]}")
            print(f"   默认值: {col_info[2]}")
            
            if col_info[1] == 'NO' and col_info[2] is not None:
                print("\n" + "=" * 60)
                print("✅ 修复成功！")
                print("\n现在可以重新运行批量创建脚本了：")
                print("   docker compose exec api python scripts/batch_create_departments_users.py")
            else:
                print("\n⚠️  修复可能不完整，请检查")
                
        except Exception as e:
            print(f"\n❌ 修复失败: {e}")
            await session.rollback()
            raise


async def main():
    await fix_department_is_active()


if __name__ == "__main__":
    asyncio.run(main())
