"""
部门管理路由（树形结构）
提供多层级部门的增删改查接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel

from src.services.department_service import DepartmentService
from src.storage.postgres.models_business import User
from server.utils.auth_middleware import get_superadmin_user, get_required_user

# 创建路由器
department = APIRouter(prefix="/departments", tags=["department"])


# =============================================================================
# === 请求和响应模型 ===
# =============================================================================


class DepartmentCreate(BaseModel):
    """创建部门请求"""

    name: str
    parent_id: int | None = None
    description: str | None = None
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    """更新部门请求"""

    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    """部门响应"""

    id: int
    name: str
    parent_id: int | None = None
    level: int
    path: str | None = None
    sort_order: int
    description: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


# =============================================================================
# === 部门管理路由 ===
# =============================================================================


@department.get("")
async def get_departments(current_user: User = Depends(get_required_user)):
    """获取所有部门（所有登录用户可访问）"""
    service = DepartmentService()
    tree = await service.get_department_tree()
    return {"success": True, "data": tree}


@department.get("/tree")
async def get_department_tree(current_user: User = Depends(get_required_user)):
    """获取部门树（所有登录用户可访问）"""
    service = DepartmentService()
    tree = await service.get_department_tree()
    return {"success": True, "data": tree}


@department.get("/{department_id}")
async def get_department_with_children(
    department_id: int,
    current_user: User = Depends(get_required_user)
):
    """获取部门及其所有子部门（所有登录用户可访问）"""
    service = DepartmentService()
    departments = await service.get_department_with_descendants(department_id)
    
    if not departments:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    return {"success": True, "data": departments}


@department.post("", status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    request: Request,
    current_user: User = Depends(get_superadmin_user),
):
    """创建新部门（支持多层级）"""
    service = DepartmentService()
    
    try:
        new_dept = await service.create_department(
            name=department_data.name,
            parent_id=department_data.parent_id,
            description=department_data.description,
            sort_order=department_data.sort_order,
        )
        
        return {"success": True, "data": new_dept, "message": "部门创建成功"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建部门失败: {str(e)}")


@department.put("/{department_id}")
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    request: Request,
    current_user: User = Depends(get_superadmin_user),
):
    """更新部门信息"""
    service = DepartmentService()
    
    try:
        updated_dept = await service.update_department(
            dept_id=department_id,
            name=department_data.name,
            description=department_data.description,
            sort_order=department_data.sort_order,
            is_active=department_data.is_active,
        )
        
        return {"success": True, "data": updated_dept, "message": "部门更新成功"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新部门失败: {str(e)}")


@department.delete("/{department_id}")
async def delete_department(
    department_id: int,
    request: Request,
    force: bool = False,
    current_user: User = Depends(get_superadmin_user),
):
    """删除部门"""
    service = DepartmentService()
    
    try:
        await service.delete_department(dept_id=department_id, force=force)
        return {"success": True, "message": "部门删除成功"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除部门失败: {str(e)}")
