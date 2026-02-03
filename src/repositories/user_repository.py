"""用户数据访问层 - Repository"""

from datetime import UTC
from datetime import datetime as dt
from typing import Annotated, Any

from sqlalchemy import func, select

from src.storage.postgres.manager import pg_manager
from src.storage.postgres.models_business import User

# 使用 naive datetime 以兼容 PostgreSQL TIMESTAMP WITHOUT TIME ZONE 列
_utc_now = dt.now(UTC).replace(tzinfo=None)


class UserRepository:
    """用户数据访问层"""

    async def get_by_id(self, id: int) -> User | None:
        """根据 ID 获取用户"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User).where(User.id == id))
            return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> User | None:
        """根据 user_id 获取用户"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        """根据手机号获取用户"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User).where(User.phone_number == phone))
            return result.scalar_one_or_none()

    async def list_users(
        self, skip: int = 0, limit: int = 100, department_id: int | None = None, role: str | None = None
    ) -> list[User]:
        """获取用户列表"""
        async with pg_manager.get_async_session_context() as session:
            query = select(User).where(User.is_deleted == 0)

            # 如果指定了部门ID，通过关系表筛选
            if department_id is not None:
                from src.storage.postgres.models_business import UserDepartmentRelation

                dept_users_subquery = (
                    select(UserDepartmentRelation.user_id)
                    .where(UserDepartmentRelation.department_id == department_id)
                    .subquery()
                )
                query = query.where(User.id.in_(select(dept_users_subquery.c.user_id)))

            if role is not None:
                query = query.where(User.role == role)

            query = query.order_by(User.id.asc()).offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def list_with_department(
        self, skip: int = 0, limit: int = 100, department_id: int | None = None, role: str | None = None
    ) -> Annotated[list[tuple[User, str | None]], "用户列表，包含主部门名称"]:
        """获取用户列表，包含主部门名称（从多对多关系表中获取）"""
        async with pg_manager.get_async_session_context() as session:
            from src.storage.postgres.models_business import Department, UserDepartmentRelation

            # 子查询：获取每个用户的主部门ID
            primary_dept_subquery = (
                select(UserDepartmentRelation.user_id, UserDepartmentRelation.department_id)
                .where(UserDepartmentRelation.is_primary == 1)
                .subquery()
            )

            # 主查询：关联用户表、主部门关系、部门表
            query = (
                select(User, Department.name.label("department_name"))
                .outerjoin(primary_dept_subquery, User.id == primary_dept_subquery.c.user_id)
                .outerjoin(Department, primary_dept_subquery.c.department_id == Department.id)
                .where(User.is_deleted == 0)
            )

            # 如果指定了部门ID，筛选属于该部门的用户（主部门或非主部门）
            if department_id is not None:
                dept_users_subquery = (
                    select(UserDepartmentRelation.user_id)
                    .where(UserDepartmentRelation.department_id == department_id)
                    .subquery()
                )
                query = query.where(User.id.in_(select(dept_users_subquery.c.user_id)))

            if role is not None:
                query = query.where(User.role == role)

            query = query.order_by(User.id.asc()).offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.all())

    async def create(self, data: dict[str, Any]) -> User:
        """创建用户"""
        async with pg_manager.get_async_session_context() as session:
            user = User(**data)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    async def update(self, id: int, data: dict[str, Any]) -> User | None:
        """更新用户"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User).where(User.id == id, User.is_deleted == 0))
            user = result.scalar_one_or_none()
            if user is None:
                return None
            for key, value in data.items():
                if key != "id":
                    setattr(user, key, value)
        return user

    async def soft_delete(self, id: int, username: str | None = None, phone_number: str | None = None) -> bool:
        """软删除用户"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User).where(User.id == id, User.is_deleted == 0))
            user = result.scalar_one_or_none()
            if user is None:
                return False
            user.is_deleted = 1

            user.deleted_at = _utc_now()
            if username:
                import hashlib

                hash_suffix = hashlib.sha256(user.user_id.encode()).hexdigest()[:4]
                user.username = f"已注销用户-{hash_suffix}"
            if phone_number:
                user.phone_number = None
        return True

    async def exists_by_user_id(self, user_id: str) -> bool:
        """检查 user_id 是否存在"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User.id).where(User.user_id == user_id))
            return result.scalar_one_or_none() is not None

    async def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否存在"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User.id).where(User.phone_number == phone))
            return result.scalar_one_or_none() is not None

    async def count(self, department_id: int | None = None) -> int:
        """统计用户数量"""
        async with pg_manager.get_async_session_context() as session:
            query = select(func.count(User.id)).where(User.is_deleted == 0)

            if department_id is not None:
                from src.storage.postgres.models_business import UserDepartmentRelation

                dept_users_subquery = (
                    select(UserDepartmentRelation.user_id)
                    .where(UserDepartmentRelation.department_id == department_id)
                    .subquery()
                )
                query = query.where(User.id.in_(select(dept_users_subquery.c.user_id)))

            result = await session.execute(query)
            return result.scalar() or 0

    async def get_all_user_ids(self) -> list[str]:
        """获取所有用户 ID"""
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(User.user_id))
            return [uid for (uid,) in result.all()]

    async def get_admin_count_in_department(self, department_id: int, exclude_user_id: int | None = None) -> int:
        """统计部门中管理员数量（通过关系表查询）"""
        async with pg_manager.get_async_session_context() as session:
            from src.storage.postgres.models_business import UserDepartmentRelation

            # 先找到属于该部门的所有用户ID
            dept_user_ids = (
                select(UserDepartmentRelation.user_id).where(UserDepartmentRelation.department_id == department_id)
            ).subquery()

            # 统计这些用户中有多少是管理员
            query = select(func.count(User.id)).where(
                User.id.in_(select(dept_user_ids.c.user_id)), User.role == "admin", User.is_deleted == 0
            )

            if exclude_user_id is not None:
                query = query.where(User.id != exclude_user_id)

            result = await session.execute(query)
            return result.scalar() or 0
