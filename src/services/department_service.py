"""
部门管理服务 - 支持树形结构的多层级部门
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.storage.postgres.manager import PostgresManager
from src.storage.postgres.models_business import Department
from src.utils import logger


class DepartmentService:
    """部门管理服务"""

    def __init__(self):
        self.db = PostgresManager()
        self.db.initialize()

    async def create_department(
        self,
        name: str,
        parent_id: int | None = None,
        description: str | None = None,
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """
        创建部门
        
        Args:
            name: 部门名称
            parent_id: 父部门ID（None表示顶层部门）
            description: 描述
            sort_order: 排序
        """
        async with self.db.get_async_session_context() as session:
            try:
                # 计算层级和路径
                level = 1
                path = None
                
                if parent_id:
                    # 查询父部门
                    parent_result = await session.execute(
                        text("SELECT id, level, path FROM departments WHERE id = :id"),
                        {"id": parent_id}
                    )
                    parent = parent_result.fetchone()
                    
                    if not parent:
                        raise ValueError(f"父部门不存在: {parent_id}")
                    
                    level = parent[1] + 1  # parent.level + 1
                    parent_path = parent[2] or str(parent[0])
                    path = f"{parent_path}/{parent_id}"
                
                # 创建部门
                result = await session.execute(
                    text("""
                        INSERT INTO departments (name, parent_id, level, path, sort_order, description)
                        VALUES (:name, :parent_id, :level, :path, :sort_order, :description)
                        RETURNING id, name, parent_id, level, path, sort_order, description, is_active, created_at, updated_at
                    """),
                    {
                        "name": name,
                        "parent_id": parent_id,
                        "level": level,
                        "path": path,
                        "sort_order": sort_order,
                        "description": description
                    }
                )
                
                row = result.fetchone()
                await session.commit()
                
                # 如果是顶层部门，更新 path 为自己的 id
                if not parent_id:
                    await session.execute(
                        text("UPDATE departments SET path = CAST(id AS VARCHAR) WHERE id = :id"),
                        {"id": row[0]}
                    )
                    await session.commit()
                    
                    # 重新查询
                    result = await session.execute(
                        text("SELECT id, name, parent_id, level, path, sort_order, description, is_active, created_at, updated_at FROM departments WHERE id = :id"),
                        {"id": row[0]}
                    )
                    row = result.fetchone()
                
                logger.info(f"Created department: {name} (id={row[0]}, level={level})")
                
                return {
                    "id": row[0],
                    "name": row[1],
                    "parent_id": row[2],
                    "level": row[3],
                    "path": row[4],
                    "sort_order": row[5],
                    "description": row[6],
                    "is_active": bool(row[7]),
                    "created_at": str(row[8]),
                    "updated_at": str(row[9]),
                }
                
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Failed to create department: {e}")
                raise ValueError(f"部门创建失败，可能名称重复: {str(e)}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create department: {e}")
                raise

    async def get_department_tree(self) -> list[dict[str, Any]]:
        """获取完整部门树（包含用户数量）"""
        async with self.db.get_async_session_context() as session:
            # 查询所有部门
            result = await session.execute(
                text("""
                    SELECT id, name, parent_id, level, path, sort_order, description, is_active
                    FROM departments
                    WHERE is_active = 1
                    ORDER BY level, sort_order, id
                """)
            )
            departments = [
                {
                    "id": row[0],
                    "name": row[1],
                    "parent_id": row[2],
                    "level": row[3],
                    "path": row[4],
                    "sort_order": row[5],
                    "description": row[6],
                    "is_active": bool(row[7]),
                }
                for row in result.fetchall()
            ]
            
            # 查询每个部门的用户数量（主部门）
            user_count_result = await session.execute(
                text("""
                    SELECT udr.department_id, COUNT(DISTINCT udr.user_id) as user_count
                    FROM user_department_relations udr
                    JOIN users u ON udr.user_id = u.id
                    WHERE udr.is_primary = 1 AND u.is_deleted = 0
                    GROUP BY udr.department_id
                """)
            )
            
            user_counts = {row[0]: row[1] for row in user_count_result.fetchall()}
            
            # 为每个部门添加用户数量
            for dept in departments:
                dept["user_count"] = user_counts.get(dept["id"], 0)
            
            return self._build_tree(departments)

    def _build_tree(self, departments: list[dict]) -> list[dict]:
        """构建树形结构"""
        dept_map = {d["id"]: {**d, "children": []} for d in departments}
        tree = []
        
        for dept in departments:
            if dept["parent_id"] is None:
                tree.append(dept_map[dept["id"]])
            else:
                parent = dept_map.get(dept["parent_id"])
                if parent:
                    parent["children"].append(dept_map[dept["id"]])
        
        return tree

    async def get_department_with_descendants(self, dept_id: int) -> list[dict[str, Any]]:
        """获取部门及其所有子部门（递归）"""
        async with self.db.get_async_session_context() as session:
            # 先查询部门本身
            dept_result = await session.execute(
                text("SELECT id, path FROM departments WHERE id = :id"),
                {"id": dept_id}
            )
            dept = dept_result.fetchone()
            
            if not dept:
                return []
            
            # 查询所有子部门（path 以该部门路径开头）
            result = await session.execute(
                text("""
                    SELECT id, name, parent_id, level, path, sort_order, description, is_active
                    FROM departments
                    WHERE id = :id OR path LIKE :pattern
                    ORDER BY level, sort_order
                """),
                {"id": dept_id, "pattern": f"{dept[1]}/%"}
            )
            
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "parent_id": row[2],
                    "level": row[3],
                    "path": row[4],
                    "sort_order": row[5],
                    "description": row[6],
                    "is_active": bool(row[7]),
                }
                for row in result.fetchall()
            ]

    async def update_department(
        self,
        dept_id: int,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any]:
        """更新部门信息"""
        async with self.db.get_async_session_context() as session:
            updates = []
            params = {"id": dept_id}
            
            if name is not None:
                updates.append("name = :name")
                params["name"] = name
            if description is not None:
                updates.append("description = :description")
                params["description"] = description
            if sort_order is not None:
                updates.append("sort_order = :sort_order")
                params["sort_order"] = sort_order
            if is_active is not None:
                updates.append("is_active = :is_active")
                params["is_active"] = 1 if is_active else 0
            
            if not updates:
                raise ValueError("没有可更新的字段")
            
            updates.append("updated_at = NOW()")
            
            await session.execute(
                text(f"UPDATE departments SET {', '.join(updates)} WHERE id = :id"),
                params
            )
            await session.commit()
            
            # 查询更新后的部门
            result = await session.execute(
                text("SELECT id, name, parent_id, level, path, sort_order, description, is_active, created_at, updated_at FROM departments WHERE id = :id"),
                {"id": dept_id}
            )
            row = result.fetchone()
            
            return {
                "id": row[0],
                "name": row[1],
                "parent_id": row[2],
                "level": row[3],
                "path": row[4],
                "sort_order": row[5],
                "description": row[6],
                "is_active": bool(row[7]),
                "created_at": str(row[8]),
                "updated_at": str(row[9]),
            }

    async def delete_department(self, dept_id: int, force: bool = False):
        """
        删除部门
        
        Args:
            dept_id: 部门ID
            force: 是否强制删除（级联删除子部门）
        """
        async with self.db.get_async_session_context() as session:
            # 检查是否有子部门
            children_result = await session.execute(
                text("SELECT COUNT(*) FROM departments WHERE parent_id = :id"),
                {"id": dept_id}
            )
            children_count = children_result.fetchone()[0]
            
            if children_count > 0 and not force:
                raise ValueError(f"该部门下有 {children_count} 个子部门，请先删除子部门或使用强制删除")
            
            # 删除部门（会级联删除子部门和关联关系）
            await session.execute(
                text("DELETE FROM departments WHERE id = :id"),
                {"id": dept_id}
            )
            await session.commit()
            
            logger.info(f"Deleted department: {dept_id}")
