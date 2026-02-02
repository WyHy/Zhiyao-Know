"""
临时修复脚本：为 User 模型添加临时属性以兼容旧代码

由于 auth_router.py 中大量使用了 user.department_id，
为了避免大规模重构，我们为 User 模型添加临时的属性方法
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.postgres.models_business import User, UserDepartmentRelation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def add_department_property_to_user():
    """
    为 User 模型动态添加 department_id 属性方法
    """
    
    # 定义获取主部门ID的方法
    async def get_primary_department_id(self, session: AsyncSession) -> int | None:
        """获取用户的主部门ID"""
        result = await session.execute(
            select(UserDepartmentRelation.department_id)
            .where(
                UserDepartmentRelation.user_id == self.id,
                UserDepartmentRelation.is_primary == 1
            )
        )
        return result.scalar_one_or_none()
    
    # 将方法附加到 User 类
    User.get_primary_department_id = get_primary_department_id
    
    print("✅ 成功为 User 模型添加 get_primary_department_id 方法")
    print("现在可以使用: await user.get_primary_department_id(session)")


if __name__ == "__main__":
    asyncio.run(add_department_property_to_user())
    print("\n这是一个概念验证脚本。")
    print("实际上我们需要在模型文件中直接添加这个方法。")
