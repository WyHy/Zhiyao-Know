"""
文件检索服务 - 支持多部门 + 关键词筛选
"""

from datetime import datetime
from typing import Any

from sqlalchemy import text

from src.services.kb_access_control_service import KBAccessControlService
from src.services.user_department_service import KBDepartmentService
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


class FileSearchService:
    """文件检索服务"""

    def __init__(self):
        self.db = PostgresManager()
        self.db.initialize()
        self.kb_dept_service = KBDepartmentService()
        self.access_control_service = KBAccessControlService()

    async def search_files(
        self,
        user_id: int,
        user_role: str = "user",
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
        # 1. 如果没有指定部门，使用用户所属部门
        if not department_ids:
            from src.services.user_department_service import UserDepartmentService
            user_dept_service = UserDepartmentService()
            user_depts = await user_dept_service.get_user_departments(user_id)
            department_ids = [d["id"] for d in user_depts]
            
            if not department_ids:
                logger.warning(f"User {user_id} has no departments")
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "files": [],
                    "department_stats": {},
                }
        
        # 2. 获取部门关联的知识库
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
        
        # 3. 过滤用户无权访问的知识库
        if user_role != "superadmin":
            denied_kb_ids = await self.access_control_service.get_user_accessible_kb_ids(user_id, user_role)
            kb_ids = [kb_id for kb_id in kb_ids if kb_id not in denied_kb_ids]
        
        if not kb_ids:
            logger.info(f"User {user_id} has no accessible knowledge bases")
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "files": [],
                "department_stats": {},
            }
        
        # 4. 构建文件查询
        async with self.db.get_async_session_context() as session:
            # 构建基础查询
            query_parts = ["""
                SELECT 
                    f.id,
                    f.file_id,
                    f.kb_id,
                    f.filename,
                    f.file_path,
                    f.file_size,
                    f.file_type,
                    f.status,
                    f.title,
                    f.summary,
                    f.tags,
                    f.created_at,
                    f.updated_at,
                    f.created_by,
                    u.username as created_by_name
                FROM kb_files f
                LEFT JOIN users u ON f.created_by = u.id
                WHERE f.kb_id = ANY(:kb_ids)
                  AND f.status = 'indexed'
            """]
            
            params = {"kb_ids": kb_ids}
            
            # 添加关键词过滤（全文检索）
            if keyword:
                query_parts.append("""
                    AND to_tsvector('simple', 
                        COALESCE(f.filename, '') || ' ' || 
                        COALESCE(f.title, '') || ' ' || 
                        COALESCE(f.summary, '')
                    ) @@ plainto_tsquery('simple', :keyword)
                """)
                params["keyword"] = keyword
            
            # 添加文件类型过滤
            if file_types:
                query_parts.append("AND f.file_type = ANY(:file_types)")
                params["file_types"] = file_types
            
            # 添加时间范围
            if date_from:
                query_parts.append("AND f.created_at >= :date_from")
                params["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            if date_to:
                query_parts.append("AND f.created_at <= :date_to")
                params["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            
            # 查询总数
            count_query = "SELECT COUNT(*) FROM kb_files f WHERE f.kb_id = ANY(:kb_ids) AND f.status = 'indexed'"
            if keyword:
                count_query += """ AND to_tsvector('simple', 
                    COALESCE(f.filename, '') || ' ' || 
                    COALESCE(f.title, '') || ' ' || 
                    COALESCE(f.summary, '')
                ) @@ plainto_tsquery('simple', :keyword)"""
            if file_types:
                count_query += " AND f.file_type = ANY(:file_types)"
            if date_from:
                count_query += " AND f.created_at >= :date_from"
            if date_to:
                count_query += " AND f.created_at <= :date_to"
            
            count_result = await session.execute(text(count_query), params)
            total = count_result.fetchone()[0]
            
            # 添加排序和分页
            valid_sort_fields = ["created_at", "filename", "file_size", "updated_at"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"
            
            order = "DESC" if order.lower() == "desc" else "ASC"
            query_parts.append(f"ORDER BY f.{sort_by} {order}")
            query_parts.append("LIMIT :limit OFFSET :offset")
            
            params["limit"] = page_size
            params["offset"] = (page - 1) * page_size
            
            # 执行查询
            result = await session.execute(text(" ".join(query_parts)), params)
            
            files = [
                {
                    "id": row[0],
                    "file_id": row[1],
                    "kb_id": row[2],
                    "filename": row[3],
                    "file_path": row[4],
                    "file_size": row[5],
                    "file_type": row[6],
                    "status": row[7],
                    "title": row[8],
                    "summary": row[9],
                    "tags": row[10] or [],
                    "created_at": str(row[11]),
                    "updated_at": str(row[12]),
                    "created_by": row[13],
                    "created_by_name": row[14],
                    "download_url": f"/api/files/{row[1]}/download",
                }
                for row in result.fetchall()
            ]
            
            # 查询部门统计
            dept_stats = await self._get_department_stats(session, kb_ids, department_ids)
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "files": files,
                "department_stats": dept_stats,
            }

    async def _get_department_stats(self, session, kb_ids: list[str], dept_ids: list[int] | None) -> dict[int, int]:
        """获取各部门的文件数统计"""
        if not dept_ids:
            return {}
        
        result = await session.execute(
            text("""
                SELECT kdr.department_id, COUNT(DISTINCT f.id) as file_count
                FROM kb_files f
                JOIN kb_department_relations kdr ON f.kb_id = kdr.kb_id
                WHERE f.kb_id = ANY(:kb_ids) 
                  AND kdr.department_id = ANY(:dept_ids)
                  AND f.status = 'indexed'
                GROUP BY kdr.department_id
            """),
            {"kb_ids": kb_ids, "dept_ids": dept_ids}
        )
        
        return {row[0]: row[1] for row in result.fetchall()}

    async def sync_file_to_db(
        self,
        file_id: str,
        kb_id: str,
        filename: str,
        file_path: str | None = None,
        file_size: int | None = None,
        file_type: str | None = None,
        status: str = "uploaded",
        created_by: int | None = None,
    ) -> dict[str, Any]:
        """
        同步文件信息到数据库（供知识库上传时调用）
        
        Args:
            file_id: 文件唯一标识
            kb_id: 所属知识库
            filename: 文件名
            file_path: MinIO路径
            file_size: 文件大小
            file_type: 文件类型
            status: 状态
            created_by: 创建人
        """
        async with self.db.get_async_session_context() as session:
            await session.execute(
                text("""
                    INSERT INTO kb_files (file_id, kb_id, filename, file_path, file_size, file_type, status, created_by)
                    VALUES (:file_id, :kb_id, :filename, :file_path, :file_size, :file_type, :status, :created_by)
                    ON CONFLICT (file_id) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        updated_at = NOW()
                """),
                {
                    "file_id": file_id,
                    "kb_id": kb_id,
                    "filename": filename,
                    "file_path": file_path,
                    "file_size": file_size,
                    "file_type": file_type,
                    "status": status,
                    "created_by": created_by,
                }
            )
            await session.commit()
            
            logger.debug(f"Synced file to db: {file_id}")
            
            return {"file_id": file_id, "status": status}

    async def update_file_status(self, file_id: str, status: str):
        """更新文件状态"""
        async with self.db.get_async_session_context() as session:
            await session.execute(
                text("UPDATE kb_files SET status = :status, updated_at = NOW() WHERE file_id = :file_id"),
                {"file_id": file_id, "status": status}
            )
            await session.commit()
