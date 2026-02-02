"""
知识库访问控制服务 - 黑名单机制
"""

from typing import Any

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager
from src.utils import logger


class KBAccessControlService:
    """知识库访问控制服务"""

    def __init__(self):
        self.db = PostgresManager()
        self.db.initialize()

    async def can_user_access_kb(self, user_id: int, kb_id: str, user_role: str = "user") -> bool:
        """
        判断用户是否可以访问知识库
        
        规则：
        1. 超级管理员可以访问所有知识库
        2. 普通用户默认可以访问所有知识库
        3. 除非该用户被显式禁止访问该知识库（黑名单）
        """
        # 1. 超级管理员全部允许
        if user_role == "superadmin":
            return True
        
        # 2. 检查黑名单
        async with self.db.get_async_session_context() as session:
            result = await session.execute(
                text("""
                    SELECT 1 FROM kb_access_control 
                    WHERE user_id = :user_id AND kb_id = :kb_id AND access_type = 'deny'
                """),
                {"user_id": user_id, "kb_id": kb_id}
            )
            is_denied = result.fetchone() is not None
        
        return not is_denied

    async def get_user_accessible_kb_ids(self, user_id: int, user_role: str = "user") -> list[str]:
        """
        获取用户可访问的知识库ID列表
        
        Returns:
            知识库ID列表（排除黑名单）
        """
        # 超级管理员返回所有知识库
        if user_role == "superadmin":
            return []  # 空列表表示无限制
        
        async with self.db.get_async_session_context() as session:
            # 查询被禁止的知识库
            result = await session.execute(
                text("""
                    SELECT kb_id FROM kb_access_control 
                    WHERE user_id = :user_id AND access_type = 'deny'
                """),
                {"user_id": user_id}
            )
            denied_kb_ids = [row[0] for row in result.fetchall()]
            
            return denied_kb_ids  # 返回黑名单列表

    async def deny_user_access(
        self,
        kb_id: str,
        user_ids: list[int],
        reason: str | None = None,
        operator_id: int | None = None
    ) -> int:
        """
        禁止用户访问知识库（添加到黑名单）
        
        Returns:
            成功添加的数量
        """
        async with self.db.get_async_session_context() as session:
            count = 0
            for user_id in user_ids:
                await session.execute(
                    text("""
                        INSERT INTO kb_access_control (kb_id, user_id, access_type, reason, created_by)
                        VALUES (:kb_id, :user_id, 'deny', :reason, :created_by)
                        ON CONFLICT (kb_id, user_id) 
                        DO UPDATE SET 
                            reason = EXCLUDED.reason,
                            created_at = NOW(),
                            created_by = EXCLUDED.created_by
                    """),
                    {
                        "kb_id": kb_id,
                        "user_id": user_id,
                        "reason": reason,
                        "created_by": operator_id
                    }
                )
                count += 1
            
            await session.commit()
            logger.info(f"Denied access to kb {kb_id} for {count} users")
            return count

    async def allow_user_access(self, kb_id: str, user_ids: list[int]) -> int:
        """
        允许用户访问知识库（从黑名单移除）
        
        Returns:
            成功移除的数量
        """
        async with self.db.get_async_session_context() as session:
            for user_id in user_ids:
                await session.execute(
                    text("DELETE FROM kb_access_control WHERE kb_id = :kb_id AND user_id = :user_id"),
                    {"kb_id": kb_id, "user_id": user_id}
                )
            
            await session.commit()
            logger.info(f"Allowed access to kb {kb_id} for {len(user_ids)} users")
            return len(user_ids)

    async def get_kb_access_list(self, kb_id: str) -> dict[str, Any]:
        """获取知识库的访问控制列表"""
        async with self.db.get_async_session_context() as session:
            # 查询被禁止的用户
            result = await session.execute(
                text("""
                    SELECT 
                        acl.user_id,
                        u.username,
                        u.user_id as user_login_id,
                        acl.reason,
                        acl.created_at,
                        acl.created_by,
                        creator.username as created_by_name
                    FROM kb_access_control acl
                    JOIN users u ON acl.user_id = u.id
                    LEFT JOIN users creator ON acl.created_by = creator.id
                    WHERE acl.kb_id = :kb_id AND acl.access_type = 'deny'
                    ORDER BY acl.created_at DESC
                """),
                {"kb_id": kb_id}
            )
            
            denied_users = [
                {
                    "user_id": row[0],
                    "username": row[1],
                    "user_login_id": row[2],
                    "reason": row[3],
                    "denied_at": str(row[4]),
                    "denied_by": row[6] if row[6] else "系统",
                }
                for row in result.fetchall()
            ]
            
            # 查询总用户数
            total_result = await session.execute(text("SELECT COUNT(*) FROM users WHERE is_deleted = 0"))
            total_users = total_result.fetchone()[0]
            
            return {
                "kb_id": kb_id,
                "total_users": total_users,
                "denied_count": len(denied_users),
                "allowed_count": total_users - len(denied_users),
                "denied_users": denied_users,
            }

    async def batch_check_access(self, user_id: int, kb_ids: list[str], user_role: str = "user") -> dict[str, bool]:
        """
        批量检查用户对多个知识库的访问权限
        
        Returns:
            {kb_id: can_access} 字典
        """
        if user_role == "superadmin":
            return {kb_id: True for kb_id in kb_ids}
        
        async with self.db.get_async_session_context() as session:
            # 一次性查询所有被禁止的知识库
            result = await session.execute(
                text("""
                    SELECT kb_id FROM kb_access_control 
                    WHERE user_id = :user_id AND access_type = 'deny' AND kb_id = ANY(:kb_ids)
                """),
                {"user_id": user_id, "kb_ids": kb_ids}
            )
            denied_set = {row[0] for row in result.fetchall()}
        
        return {kb_id: kb_id not in denied_set for kb_id in kb_ids}
