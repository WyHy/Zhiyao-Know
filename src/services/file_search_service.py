"""
文件检索服务 - 支持多部门 + 关键词筛选
"""

from datetime import datetime
from typing import Any

from src import knowledge_base
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
            # 使用 check_accessible 检查每个知识库的访问权限
            from src.repositories.knowledge_base_repository import KnowledgeBaseRepository
            kb_repo = KnowledgeBaseRepository()
            
            accessible_kb_ids = []
            for kb_id in kb_ids:
                try:
                    # 构建用户信息
                    user_info = {
                        "role": user_role,
                        "user_id": user_id,
                        "department_id": None  # 会在 check_accessible 中查询
                    }
                    
                    # 检查访问权限（包含黑名单检查）
                    can_access = await knowledge_base.check_accessible(user_info, kb_id)
                    if can_access:
                        accessible_kb_ids.append(kb_id)
                except Exception as e:
                    logger.error(f"Error checking access for kb {kb_id}: {e}")
                    continue
            
            kb_ids = accessible_kb_ids
        
        if not kb_ids:
            logger.info(f"User {user_id} has no accessible knowledge bases")
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "files": [],
                "department_stats": {},
            }
        
        # 4. 从知识库中获取所有文件
        all_files = []
        kb_name_map = {}  # 用于记录知识库名称
        
        for kb_id in kb_ids:
            try:
                db_info = await knowledge_base.get_database_info(kb_id)
                if not db_info:
                    continue
                
                kb_name_map[kb_id] = db_info.get("name", "")
                files = db_info.get("files", {})
                
                for file_id, file_info in files.items():
                    # 只包含状态为 indexed 或 done 的文件
                    file_status = file_info.get("status", "")
                    if file_status not in ["indexed", "done"]:
                        continue
                    
                    file_data = {
                        "file_id": file_id,
                        "kb_id": kb_id,
                        "kb_name": db_info.get("name", ""),
                        "filename": file_info.get("filename", ""),
                        "file_path": file_info.get("path", ""),
                        "file_size": 0,  # 知识库元数据中没有文件大小
                        "file_type": file_info.get("type", "").lower(),
                        "status": file_status,
                        "created_at": file_info.get("created_at", ""),
                        "updated_at": file_info.get("created_at", ""),
                        "download_url": f"/api/knowledge/files/{file_id}/download",
                    }
                    all_files.append(file_data)
            except Exception as e:
                logger.error(f"Error fetching files from kb {kb_id}: {e}")
                continue
        
        # 5. 应用筛选条件
        filtered_files = all_files
        
        # 关键词筛选
        if keyword:
            keyword_lower = keyword.lower()
            filtered_files = [
                f for f in filtered_files
                if keyword_lower in f["filename"].lower()
            ]
        
        # 文件类型筛选
        if file_types:
            file_types_lower = [ft.lower() for ft in file_types]
            filtered_files = [
                f for f in filtered_files
                if f["file_type"] in file_types_lower
            ]
        
        # 时间范围筛选
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                filtered_files = [
                    f for f in filtered_files
                    if f["created_at"] and datetime.fromisoformat(
                        f["created_at"].replace("Z", "+00:00")
                    ) >= date_from_dt
                ]
            except Exception as e:
                logger.warning(f"Invalid date_from format: {date_from}, {e}")
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                filtered_files = [
                    f for f in filtered_files
                    if f["created_at"] and datetime.fromisoformat(
                        f["created_at"].replace("Z", "+00:00")
                    ) <= date_to_dt
                ]
            except Exception as e:
                logger.warning(f"Invalid date_to format: {date_to}, {e}")
        
        # 6. 排序
        valid_sort_fields = ["created_at", "filename", "file_size", "updated_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        reverse = order.lower() == "desc"
        
        try:
            if sort_by == "filename":
                filtered_files.sort(key=lambda x: x["filename"], reverse=reverse)
            elif sort_by == "file_size":
                filtered_files.sort(key=lambda x: x["file_size"] or 0, reverse=reverse)
            else:  # created_at or updated_at
                filtered_files.sort(
                    key=lambda x: x.get(sort_by, "") or "",
                    reverse=reverse
                )
        except Exception as e:
            logger.warning(f"Sort error: {e}")
        
        # 7. 分页
        total = len(filtered_files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = filtered_files[start:end]
        
        # 8. 获取部门统计
        dept_stats = await self._get_department_stats_from_kb(kb_ids, department_ids)
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "files": page_files,
            "department_stats": dept_stats,
        }

    async def _get_department_stats_from_kb(self, kb_ids: list[str], dept_ids: list[int] | None) -> dict[int, int]:
        """从知识库获取各部门的文件数统计"""
        if not dept_ids:
            return {}
        
        # 统计每个部门关联的知识库中的文件数
        dept_file_counts = {dept_id: 0 for dept_id in dept_ids}
        
        # 获取部门-知识库关联
        async with self.db.get_async_session_context() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT department_id, kb_id
                    FROM kb_department_relations
                    WHERE department_id = ANY(:dept_ids)
                      AND kb_id = ANY(:kb_ids)
                """),
                {"dept_ids": dept_ids, "kb_ids": kb_ids}
            )
            dept_kb_relations = result.fetchall()
        
        # 为每个部门统计文件数
        for dept_id, kb_id in dept_kb_relations:
            try:
                db_info = await knowledge_base.get_database_info(kb_id)
                if db_info:
                    files = db_info.get("files", {})
                    # 只统计 status='indexed' 或 'done' 的文件
                    file_count = sum(
                        1 for f in files.values()
                        if f.get("status") in ["indexed", "done"]
                    )
                    dept_file_counts[dept_id] += file_count
            except Exception as e:
                logger.error(f"Error counting files for dept {dept_id}, kb {kb_id}: {e}")
        
        return dept_file_counts
