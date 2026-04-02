"""
文件检索服务 - 支持多部门 + 关键词筛选
"""

from datetime import datetime
from typing import Any

from src import knowledge_base
from src.services.user_department_service import KBDepartmentService
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


class FileSearchService:
    """文件检索服务"""

    def __init__(self):
        self.db = PostgresManager()
        self.db.initialize()
        self.kb_dept_service = KBDepartmentService()

    async def search_files(
        self,
        user_id: int,
        user_role: str = "user",
        user_department_id: int | None = None,
        department_ids: list[int] | None = None,
        include_subdepts: bool = True,
        keyword: str | None = None,
        file_types: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> dict[str, Any]:
        """
        多部门文件检索（带权限控制）
        
        Args:
            user_id: 用户ID
            user_role: 用户角色
            department_ids: 部门ID列表（None表示使用用户所属部门）
            include_subdepts: 是否包含子部门
            keyword: 文件名关键词
            file_types: 文件类型筛选
            date_from: 开始时间
            date_to: 结束时间
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序方向
        """
        # 1. 处理部门筛选逻辑
        # 如果指定了部门，则按部门筛选
        # 如果没有指定部门，则显示用户有权访问的所有知识库文件
        kb_ids = []
        
        if department_ids:
            # 指定了部门：获取这些部门关联的知识库
            kb_ids = await self.kb_dept_service.get_kb_ids_by_departments(
                department_ids,
                include_subdepts=include_subdepts
            )
            
            if not kb_ids:
                logger.info(f"No knowledge bases found for departments {department_ids}")
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "files": [],
                    "department_stats": {},
                }
        else:
            # 没有指定部门：获取所有知识库，稍后根据用户权限过滤
            all_databases = await knowledge_base.get_databases()
            kb_ids = [db.get("db_id") for db in all_databases.get("databases", []) if db.get("db_id")]
            
            if not kb_ids:
                logger.info("No knowledge bases found in the system")
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "files": [],
                    "department_stats": {},
                }
        
        # 2. 过滤用户无权访问的知识库
        if user_role != "superadmin":
            user_info = {
                "role": user_role,
                "user_id": user_id,
                "department_id": user_department_id,
            }
            accessible_databases = await knowledge_base.get_databases_by_user(user_info)
            accessible_kb_ids = {
                db.get("db_id")
                for db in accessible_databases.get("databases", [])
                if db.get("db_id")
            }
            kb_ids = [kb_id for kb_id in kb_ids if kb_id in accessible_kb_ids]
        
        if not kb_ids:
            logger.info(f"User {user_id} has no accessible knowledge bases")
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "files": [],
                "department_stats": {},
            }
        
        # 4. 从 knowledge_files 表获取文件
        from sqlalchemy import text
        
        all_files = []
        
        async with self.db.get_async_session_context() as session:
            kb_list_str = ", ".join([f"'{kb_id}'" for kb_id in kb_ids])

            # 构建查询条件
            where_conditions = [f"kf.db_id IN ({kb_list_str})", "kf.is_folder = false"]
            query_params = {}

            # 关键词筛选（模糊搜索）
            if keyword:
                where_conditions.append("(kf.filename ILIKE :keyword OR kb.name ILIKE :keyword)")
                query_params["keyword"] = f"%{keyword}%"

            # 文件类型筛选
            if file_types:
                types_list = ", ".join([f"'{ft}'" for ft in file_types])
                where_conditions.append(f"kf.file_type IN ({types_list})")

            # 时间范围筛选
            if date_from:
                where_conditions.append("kf.created_at >= :date_from")
                query_params["date_from"] = date_from

            if date_to:
                where_conditions.append("kf.created_at <= :date_to")
                query_params["date_to"] = date_to

            sort_field_map = {
                "created_at": "kf.created_at",
                "updated_at": "kf.updated_at",
                "filename": "kf.filename",
                "file_size": "kf.file_size",
            }
            sort_field = sort_field_map.get(sort_by, "kf.created_at")
            sort_order = "ASC" if str(order).lower() == "asc" else "DESC"

            where_clause = " AND ".join(where_conditions)

            # 查询文件（从 knowledge_files 表）
            query = f"""
                SELECT 
                    kf.file_id, kf.db_id, kb.name AS kb_name, kf.filename, kf.path, kf.file_size,
                    kf.file_type, kf.status, kf.created_at, kf.updated_at, kf.created_by
                FROM knowledge_files kf
                JOIN knowledge_bases kb ON kb.db_id = kf.db_id
                WHERE {where_clause}
                ORDER BY {sort_field} {sort_order}
            """

            result = await session.execute(text(query), query_params)
            rows = result.fetchall()

            logger.info(f"Found {len(rows)} files from knowledge_files table")

            # 转换为字典格式
            for row in rows:
                file_data = {
                    "file_id": row[0],
                    "kb_id": row[1],
                    "kb_name": row[2] or "未知知识库",
                    "filename": row[3],
                    "file_path": row[4],
                    "file_size": row[5] or 0,
                    "file_type": row[6] or "",
                    "status": row[7],
                    "created_at": row[8].isoformat() if row[8] else "",
                    "updated_at": row[9].isoformat() if row[9] else "",
                    "created_by": row[10],
                    "download_url": f"/api/knowledge/files/{row[0]}/download",
                }
                all_files.append(file_data)
        
        # 5. 分页处理
        total = len(all_files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = all_files[start:end]
        
        # 6. 获取部门统计（部门筛选时才返回）
        dept_stats = await self._get_department_stats_from_kb(kb_ids, department_ids)
        
        # 7. 统计涉及的知识库和部门
        kb_count = len(set(f["kb_id"] for f in all_files))
        dept_count = len(department_ids) if department_ids else 0
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "files": page_files,
            "kb_count": kb_count,
            "dept_count": dept_count,
            "department_stats": dept_stats,
        }

    async def _get_department_stats_from_kb(self, kb_ids: list[str], dept_ids: list[int] | None) -> dict[int, int]:
        """从知识库获取各部门的文件数统计"""
        if not dept_ids:
            return {}

        dept_file_counts = {dept_id: 0 for dept_id in dept_ids}

        # 直接在数据库中聚合，避免逐库读取元数据导致慢查询
        async with self.db.get_async_session_context() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT kdr.department_id, COUNT(*) AS file_count
                    FROM kb_department_relations kdr
                    JOIN knowledge_files kf ON kf.db_id = kdr.kb_id
                    WHERE kdr.department_id = ANY(:dept_ids)
                      AND kdr.kb_id = ANY(:kb_ids)
                      AND kf.is_folder = false
                    GROUP BY kdr.department_id
                """),
                {"dept_ids": dept_ids, "kb_ids": kb_ids}
            )
            for dept_id, file_count in result.fetchall():
                dept_file_counts[dept_id] = file_count

        return dept_file_counts
