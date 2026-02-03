#!/usr/bin/env python3
"""
清理重复部门并重新分配用户
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def deduplicate_departments():
    """清理重复的部门数据"""
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 1. 找出重复的部门（同一父部门下同名的）
        result = await session.execute(
            text("""
                SELECT name, parent_id, COUNT(*) as cnt, ARRAY_AGG(id ORDER BY id) as ids
                FROM departments
                GROUP BY name, parent_id
                HAVING COUNT(*) > 1
                ORDER BY cnt DESC
            """)
        )
        duplicates = result.fetchall()
        
        if not duplicates:
            logger.info("✅ 没有发现重复的部门")
            return
        
        logger.info(f"🔍 发现 {len(duplicates)} 组重复部门:")
        
        for row in duplicates:
            name, parent_id, count, ids = row
            parent_name = "根目录" if parent_id is None else f"父部门ID={parent_id}"
            logger.info(f"  - '{name}' ({parent_name}): {count} 个重复, IDs={ids}")
            
            # 保留最早的（ID最小的），删除其他的
            keep_id = ids[0]
            delete_ids = ids[1:]
            
            logger.info(f"    保留: {keep_id}, 删除: {delete_ids}")
            
            # 2. 迁移数据：将要删除的部门的关联数据迁移到保留的部门
            
            # 2.1 更新子部门的 parent_id
            await session.execute(
                text("UPDATE departments SET parent_id = :keep_id WHERE parent_id = ANY(:delete_ids)"),
                {"keep_id": keep_id, "delete_ids": delete_ids}
            )
            
            # 2.2 迁移用户-部门关联
            for delete_id in delete_ids:
                # 获取该部门的所有用户
                users_result = await session.execute(
                    text("""
                        SELECT user_id, is_primary
                        FROM user_department_relations
                        WHERE department_id = :dept_id
                    """),
                    {"dept_id": delete_id}
                )
                users = users_result.fetchall()
                
                for user_id, is_primary in users:
                    # 检查用户是否已经关联到保留的部门
                    existing = await session.execute(
                        text("""
                            SELECT 1 FROM user_department_relations
                            WHERE user_id = :user_id AND department_id = :keep_id
                        """),
                        {"user_id": user_id, "keep_id": keep_id}
                    )
                    
                    if not existing.fetchone():
                        # 不存在则添加关联
                        await session.execute(
                            text("""
                                INSERT INTO user_department_relations (user_id, department_id, is_primary)
                                VALUES (:user_id, :dept_id, :is_primary)
                                ON CONFLICT (user_id, department_id) DO NOTHING
                            """),
                            {"user_id": user_id, "dept_id": keep_id, "is_primary": is_primary}
                        )
                        logger.info(f"      迁移用户 {user_id} 到部门 {keep_id}")
            
            # 2.3 迁移知识库-部门关联
            kb_result = await session.execute(
                text("""
                    SELECT kb_id FROM kb_department_relations
                    WHERE department_id = ANY(:delete_ids)
                """),
                {"delete_ids": delete_ids}
            )
            kb_ids = [row[0] for row in kb_result.fetchall()]
            
            for kb_id in kb_ids:
                # 检查是否已关联
                existing = await session.execute(
                    text("""
                        SELECT 1 FROM kb_department_relations
                        WHERE kb_id = :kb_id AND department_id = :keep_id
                    """),
                    {"kb_id": kb_id, "keep_id": keep_id}
                )
                
                if not existing.fetchone():
                    await session.execute(
                        text("""
                            INSERT INTO kb_department_relations (kb_id, department_id)
                            VALUES (:kb_id, :dept_id)
                            ON CONFLICT (kb_id, department_id) DO NOTHING
                        """),
                        {"kb_id": kb_id, "dept_id": keep_id}
                    )
            
            # 2.4 删除重复的部门关联记录
            await session.execute(
                text("DELETE FROM user_department_relations WHERE department_id = ANY(:delete_ids)"),
                {"delete_ids": delete_ids}
            )
            await session.execute(
                text("DELETE FROM kb_department_relations WHERE department_id = ANY(:delete_ids)"),
                {"delete_ids": delete_ids}
            )
            
            # 2.5 删除重复的部门
            await session.execute(
                text("DELETE FROM departments WHERE id = ANY(:delete_ids)"),
                {"delete_ids": delete_ids}
            )
            
            logger.info(f"    ✅ 已删除重复部门: {delete_ids}")
        
        await session.commit()
        logger.info("✅ 部门去重完成")
        
        # 3. 显示清理后的部门统计
        dept_count_result = await session.execute(
            text("SELECT COUNT(*) FROM departments")
        )
        dept_count = dept_count_result.fetchone()[0]
        logger.info(f"📊 当前部门总数: {dept_count}")


async def reassign_users_to_departments():
    """重新为所有用户分配部门（确保数据一致性）"""
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 统计用户-部门关联
        result = await session.execute(
            text("""
                SELECT 
                    COUNT(DISTINCT udr.user_id) as total_users,
                    COUNT(*) as total_relations
                FROM user_department_relations udr
                JOIN users u ON udr.user_id = u.id
                WHERE u.is_deleted = 0
            """)
        )
        row = result.fetchone()
        logger.info(f"📊 用户统计: {row[0]} 个用户, {row[1]} 个部门关联")
        
        # 确保所有用户都有主部门
        users_without_primary = await session.execute(
            text("""
                SELECT u.id, u.username
                FROM users u
                WHERE u.is_deleted = 0
                AND NOT EXISTS (
                    SELECT 1 FROM user_department_relations udr
                    WHERE udr.user_id = u.id AND udr.is_primary = 1
                )
            """)
        )
        
        users_need_primary = users_without_primary.fetchall()
        if users_need_primary:
            logger.info(f"⚠️  {len(users_need_primary)} 个用户没有主部门，正在修复...")
            
            for user_id, username in users_need_primary:
                # 获取用户的第一个部门作为主部门
                first_dept = await session.execute(
                    text("""
                        SELECT department_id FROM user_department_relations
                        WHERE user_id = :user_id
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                )
                dept_row = first_dept.fetchone()
                
                if dept_row:
                    # 设置为主部门
                    await session.execute(
                        text("""
                            UPDATE user_department_relations
                            SET is_primary = 1
                            WHERE user_id = :user_id AND department_id = :dept_id
                        """),
                        {"user_id": user_id, "dept_id": dept_row[0]}
                    )
                    logger.info(f"  ✅ 为用户 {username} 设置主部门: {dept_row[0]}")
                else:
                    # 用户没有任何部门，分配到默认部门
                    default_dept = await session.execute(
                        text("SELECT id FROM departments WHERE name = '默认部门' LIMIT 1")
                    )
                    default_row = default_dept.fetchone()
                    
                    if default_row:
                        await session.execute(
                            text("""
                                INSERT INTO user_department_relations (user_id, department_id, is_primary)
                                VALUES (:user_id, :dept_id, 1)
                                ON CONFLICT (user_id, department_id) DO UPDATE SET is_primary = 1
                            """),
                            {"user_id": user_id, "dept_id": default_row[0]}
                        )
                        logger.info(f"  ✅ 为用户 {username} 分配默认部门")
        else:
            logger.info("✅ 所有用户都已有主部门")
        
        await session.commit()
        logger.info("✅ 用户部门分配完成")


async def main():
    logger.info("=" * 60)
    logger.info("开始清理重复部门并重新分配用户")
    logger.info("=" * 60)
    
    try:
        await deduplicate_departments()
        await reassign_users_to_departments()
        
        logger.info("=" * 60)
        logger.info("✅ 全部完成!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
