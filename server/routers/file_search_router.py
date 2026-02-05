"""
文件检索路由 - 支持多部门检索
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.services.file_search_service import FileSearchService
from src.storage.postgres.models_business import User
from server.utils.auth_middleware import get_current_user

# 创建路由器
file_search = APIRouter(prefix="/files", tags=["file-search"])


# =============================================================================
# === 请求和响应模型 ===
# =============================================================================


class FileSearchRequest(BaseModel):
    """文件搜索请求"""
    
    department_ids: list[int] | None = None  # 部门ID列表，None=用户所属部门
    include_subdepts: bool = True  # 是否包含子部门
    keyword: str | None = None  # 文件名关键词
    file_types: list[str] | None = None  # 文件类型筛选
    date_from: str | None = None  # 开始时间
    date_to: str | None = None  # 结束时间
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"  # created_at, filename, file_size, updated_at
    order: str = "desc"  # asc, desc


# =============================================================================
# === 文件检索路由 ===
# =============================================================================


@file_search.post("/search")
async def search_files(
    search_req: FileSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    多部门文件检索
    
    - 支持按部门筛选（默认使用用户所属部门）
    - 支持关键词搜索（全文检索）
    - 支持文件类型、时间范围筛选
    - 自动过滤用户无权访问的知识库
    """
    service = FileSearchService()
    
    try:
        result = await service.search_files(
            user_id=current_user.id,
            user_role=current_user.role,
            department_ids=search_req.department_ids,
            include_subdepts=search_req.include_subdepts,
            keyword=search_req.keyword,
            file_types=search_req.file_types,
            date_from=search_req.date_from,
            date_to=search_req.date_to,
            page=search_req.page,
            page_size=search_req.page_size,
            sort_by=search_req.sort_by,
            order=search_req.order,
        )
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@file_search.get("/search")
async def search_files_get(
    department_ids: str | None = Query(None, description="部门ID列表，逗号分隔"),
    include_subdepts: bool = Query(True, description="是否包含子部门"),
    keyword: str | None = Query(None, description="文件名关键词"),
    file_types: str | None = Query(None, description="文件类型，逗号分隔"),
    date_from: str | None = Query(None, description="开始时间 ISO格式"),
    date_to: str | None = Query(None, description="结束时间 ISO格式"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
):
    """
    多部门文件检索（GET方式）
    
    Query参数：
    - department_ids: 部门ID列表，如 "1,2,3"
    - include_subdepts: 是否包含子部门
    - keyword: 关键词
    - file_types: 文件类型，如 "pdf,docx"
    - date_from/date_to: 时间范围
    - page/page_size: 分页
    - sort_by/order: 排序
    """
    service = FileSearchService()
    
    try:
        # 解析参数
        dept_ids = None
        if department_ids:
            dept_ids = [int(x.strip()) for x in department_ids.split(",") if x.strip()]
        
        file_type_list = None
        if file_types:
            file_type_list = [x.strip() for x in file_types.split(",") if x.strip()]
        
        result = await service.search_files(
            user_id=current_user.id,
            user_role=current_user.role,
            department_ids=dept_ids,
            include_subdepts=include_subdepts,
            keyword=keyword,
            file_types=file_type_list,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
        )
        
        return {"success": True, "data": result}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@file_search.get("/my-departments")
async def get_my_searchable_departments(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户可用于检索的部门列表"""
    from src.storage.postgres.manager import pg_manager
    from sqlalchemy import text
    
    try:
        # 直接查询用户所属部门
        department = None
        if current_user.department_id:
            async with pg_manager.get_async_session_context() as session:
                result = await session.execute(
                    text("SELECT id, name, parent_id, level, path FROM departments WHERE id = :dept_id AND is_active = 1"),
                    {"dept_id": current_user.department_id}
                )
                row = result.fetchone()
                if row:
                    department = {
                        "id": row[0],
                        "name": row[1],
                        "parent_id": row[2],
                        "level": row[3],
                        "path": row[4],
                    }
        
        return {
            "success": True,
            "data": {
                "user_id": current_user.id,
                "departments": [department] if department else [],
                "department": department,
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@file_search.get("/stats")
async def get_file_stats(
    department_ids: str | None = Query(None, description="部门ID列表，逗号分隔"),
    current_user: User = Depends(get_current_user),
):
    """
    获取文件统计信息
    
    返回用户可访问的知识库和文件数量统计
    """
    from src.services.user_department_service import KBDepartmentService
    from src.services.kb_access_control_service import KBAccessControlService
    
    try:
        # 解析部门ID
        dept_ids = None
        if department_ids:
            dept_ids = [int(x.strip()) for x in department_ids.split(",") if x.strip()]
        
        # 如果没指定部门，使用用户所属部门
        if not dept_ids and current_user.department_id:
            dept_ids = [current_user.department_id]
        
        if not dept_ids:
            return {
                "success": True,
                "data": {
                    "total_kbs": 0,
                    "accessible_kbs": 0,
                    "total_files": 0,
                }
            }
        
        # 获取部门关联的知识库
        kb_dept_service = KBDepartmentService()
        kb_ids = await kb_dept_service.get_kb_ids_by_departments(dept_ids, include_subdepts=True)
        
        # 过滤用户无权访问的知识库
        access_service = KBAccessControlService()
        if current_user.role != "superadmin":
            denied_kb_ids = await access_service.get_user_accessible_kb_ids(current_user.id, current_user.role)
            accessible_kb_ids = [kb_id for kb_id in kb_ids if kb_id not in denied_kb_ids]
        else:
            accessible_kb_ids = kb_ids
        
        # 查询文件数量（从 knowledge_files 表）
        from src.storage.postgres.manager import pg_manager
        from sqlalchemy import text
        
        async with pg_manager.get_async_session_context() as session:
            if accessible_kb_ids:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM knowledge_files WHERE db_id = ANY(:kb_ids) AND status IN ('indexed', 'done') AND is_folder = false"),
                    {"kb_ids": accessible_kb_ids}
                )
                file_count = result.fetchone()[0]
            else:
                file_count = 0
        
        return {
            "success": True,
            "data": {
                "total_kbs": len(kb_ids),
                "accessible_kbs": len(accessible_kb_ids),
                "total_files": file_count,
                "department_ids": dept_ids,
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")
