"""
同步用户主部门到 User.department_id 字段

由于旧代码仍在使用 User.department_id 字段，
我们需要将新的 user_department_relations 表中的主部门同步回去
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select, update
from src.storage.postgres.manager import PostgresManager
from src.storage.postgres.models_business import User, UserDepartmentRelation


async def sync_primary_department_to_user():
    """将主部门同步到 User.department_id"""
    db = PostgresManager()
    db.initialize()
    
    print("🔄 开始同步用户主部门...\n")
    
    async with db.get_async_session_context() as session:
        # 获取所有用户的主部门关系
        result = await session.execute(
            select(UserDepartmentRelation)
            .where(UserDepartmentRelation.is_primary == 1)
        )
        
        primary_relations = result.scalars().all()
        
        print(f"📊 找到 {len(primary_relations)} 个主部门关系\n")
        
        update_count = 0
        for relation in primary_relations:
            # 更新对应用户的 department_id
            await session.execute(
                update(User)
                .where(User.id == relation.user_id)
                .values(department_id=relation.department_id)
            )
            
            # 获取用户名用于显示
            user_result = await session.execute(
                select(User.username, User.user_id)
                .where(User.id == relation.user_id)
            )
            user_data = user_result.first()
            
            if user_data:
                # 获取部门名
                dept_result = await session.execute(
                    text("SELECT name FROM departments WHERE id = :dept_id"),
                    {"dept_id": relation.department_id}
                )
                dept_name = dept_result.scalar_one_or_none()
                
                print(f"✅ {user_data.username:15s} (ID:{relation.user_id:2d}) -> 部门: {dept_name}")
                update_count += 1
        
        await session.commit()
        
        print(f"\n✅ 同步完成！更新了 {update_count} 个用户的部门字段")
        
        # 验证结果
        print("\n" + "=" * 60)
        print("📋 验证同步结果:\n")
        
        result = await session.execute(
            text("""
                SELECT 
                    u.id,
                    u.username,
                    u.department_id as old_field,
                    d.name as dept_name
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                WHERE u.is_deleted = 0
                ORDER BY u.id
                LIMIT 10
            """)
        )
        
        rows = result.fetchall()
        for row in rows:
            print(f"用户 {row[0]:2d} | {row[1]:15s} | 部门ID: {row[2] or 'NULL':>2s} | 部门: {row[3] or '无'}")
        
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(sync_primary_department_to_user())
    print("\n🎉 部门字段同步完成！现在前端应该能正确显示用户部门了！")
