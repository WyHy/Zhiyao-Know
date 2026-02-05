"""
知识库-部门关联服务
"""

from typing import Any

from sqlalchemy import text

from src.storage.postgres.manager import PostgresManager
from src.utils import logger


class KBDepartmentService:
    """知识库-部门关联服务"""

    def __init__(self):
        self.db = PostgresManager()
        self.db.initialize()

    async def add_kb_departments(
        self,
        kb_id: str,
        department_ids: list[int],
        replace: bool = False
    ) -> list[dict[str, Any]]:
        """
        为知识库添加部门标签
        
        Args:
            kb_id: 知识库ID
            department_ids: 部门ID列表
            replace: 是否替换现有标签（True=替换，False=追加）
        """
        async with self.db.get_async_session_context() as session:
            # 如果是替换模式，先删除所有现有标签
            if replace:
                await session.execute(
                    text("DELETE FROM kb_department_relations WHERE kb_id = :kb_id"),
                    {"kb_id": kb_id}
                )
            
            # 添加新标签
            for dept_id in department_ids:
                await session.execute(
                    text("""
                        INSERT INTO kb_department_relations (kb_id, department_id)
                        VALUES (:kb_id, :dept_id)
                        ON CONFLICT (kb_id, department_id) DO NOTHING
                    """),
                    {"kb_id": kb_id, "dept_id": dept_id}
                )
            
            await session.commit()
            logger.info(f"Added {len(department_ids)} departments to kb {kb_id}")
            
            # 返回更新后的部门列表
            return await self.get_kb_departments(kb_id)

    async def get_kb_departments(self, kb_id: str) -> list[dict[str, Any]]:
        """获取知识库的部门标签"""
        async with self.db.get_async_session_context() as session:
            result = await session.execute(
                text("""
                    SELECT 
                        d.id, d.name, d.parent_id, d.level, d.path, d.description
                    FROM kb_department_relations kdr
                    JOIN departments d ON kdr.department_id = d.id
                    WHERE kdr.kb_id = :kb_id AND d.is_active = 1
                    ORDER BY d.level, d.sort_order
                """),
                {"kb_id": kb_id}
            )
            
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "parent_id": row[2],
                    "level": row[3],
                    "path": row[4],
                    "description": row[5],
                }
                for row in result.fetchall()
            ]

    async def remove_kb_department(self, kb_id: str, department_id: int):
        """移除知识库的部门标签"""
        async with self.db.get_async_session_context() as session:
            await session.execute(
                text("DELETE FROM kb_department_relations WHERE kb_id = :kb_id AND department_id = :dept_id"),
                {"kb_id": kb_id, "dept_id": department_id}
            )
            await session.commit()
            logger.info(f"Removed department {department_id} from kb {kb_id}")

    async def get_kb_ids_by_departments(
        self,
        department_ids: list[int],
        include_subdepts: bool = True
    ) -> list[str]:
        """
        根据部门获取知识库ID列表
        
        Args:
            department_ids: 部门ID列表
            include_subdepts: 是否包含子部门的知识库
        """
        async with self.db.get_async_session_context() as session:
            if include_subdepts:
                # 扩展到所有子部门
                all_dept_ids = await self._expand_departments(session, department_ids)
            else:
                all_dept_ids = department_ids
            
            # 查询这些部门关联的知识库
            result = await session.execute(
                text("""
                    SELECT DISTINCT kb_id 
                    FROM kb_department_relations 
                    WHERE department_id = ANY(:dept_ids)
                """),
                {"dept_ids": all_dept_ids}
            )
            
            return [row[0] for row in result.fetchall()]

    async def _expand_departments(self, session, dept_ids: list[int]) -> list[int]:
        """扩展部门列表，包含所有子部门"""
        all_ids = set(dept_ids)
        
        for dept_id in dept_ids:
            # 查询部门路径
            dept_result = await session.execute(
                text("SELECT path FROM departments WHERE id = :id"),
                {"id": dept_id}
            )
            dept = dept_result.fetchone()
            
            if dept and dept[0]:
                # 查询所有子部门
                subdepts_result = await session.execute(
                    text("SELECT id FROM departments WHERE path LIKE :pattern"),
                    {"pattern": f"{dept[0]}/%"}
                )
                all_ids.update([row[0] for row in subdepts_result.fetchall()])
        
        return list(all_ids)
