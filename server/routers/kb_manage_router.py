"""
知识库管理路由扩展 - 部门关联和访问控制
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.services.user_department_service import KBDepartmentService
from src.services.kb_agent_binding_service import KBAgentBindingService
from src.services.kb_access_control_service import KBAccessControlService
from src.storage.postgres.models_business import User
from server.utils.auth_middleware import get_admin_user, get_superadmin_user

# 创建路由器
kb_manage = APIRouter(prefix="/kb-manage", tags=["kb-manage"])


# =============================================================================
# === 请求和响应模型 ===
# =============================================================================


class KBDepartmentAdd(BaseModel):
    """为知识库添加部门标签"""
    
    department_ids: list[int]
    replace: bool = False  # 是否替换现有标签


class KBAccessDeny(BaseModel):
    """禁止用户访问知识库"""
    
    user_ids: list[int]
    reason: str | None = None


class KBAccessAllow(BaseModel):
    """允许用户访问知识库"""
    
    user_ids: list[int]


class KBAgentBind(BaseModel):
    """绑定知识库到智能体"""

    agent_ids: list[str]
    replace: bool = False


# =============================================================================
# === 知识库-部门关联路由 ===
# =============================================================================


@kb_manage.post("/{kb_id}/departments")
async def add_kb_departments(
    kb_id: str,
    data: KBDepartmentAdd,
    current_user: User = Depends(get_admin_user),
):
    """为知识库添加部门标签"""
    service = KBDepartmentService()
    
    try:
        kb_depts = await service.add_kb_departments(
            kb_id=kb_id,
            department_ids=data.department_ids,
            replace=data.replace,
        )
        
        return {"success": True, "data": kb_depts, "message": "部门标签更新成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加部门失败: {str(e)}")


@kb_manage.get("/{kb_id}/departments")
async def get_kb_departments(
    kb_id: str,
    current_user: User = Depends(get_admin_user),
):
    """获取知识库的部门标签"""
    service = KBDepartmentService()
    kb_depts = await service.get_kb_departments(kb_id)
    
    return {"success": True, "data": kb_depts}


@kb_manage.delete("/{kb_id}/departments/{department_id}")
async def remove_kb_department(
    kb_id: str,
    department_id: int,
    current_user: User = Depends(get_admin_user),
):
    """移除知识库的部门标签"""
    service = KBDepartmentService()
    
    try:
        await service.remove_kb_department(kb_id, department_id)
        return {"success": True, "message": "部门标签移除成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除部门失败: {str(e)}")


@kb_manage.post("/departments/search-kbs")
async def search_kbs_by_departments(
    department_ids: list[int],
    include_subdepts: bool = True,
    current_user: User = Depends(get_admin_user),
):
    """根据部门查询知识库"""
    service = KBDepartmentService()
    
    try:
        kb_ids = await service.get_kb_ids_by_departments(
            department_ids=department_ids,
            include_subdepts=include_subdepts,
        )
        
        return {"success": True, "data": kb_ids}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# =============================================================================
# === 知识库访问控制路由 ===
# =============================================================================


@kb_manage.post("/{kb_id}/access/deny")
async def deny_kb_access(
    kb_id: str,
    data: KBAccessDeny,
    current_user: User = Depends(get_superadmin_user),
):
    """禁止用户访问知识库（添加到黑名单）"""
    service = KBAccessControlService()
    
    try:
        count = await service.deny_user_access(
            kb_id=kb_id,
            user_ids=data.user_ids,
            reason=data.reason,
            operator_id=current_user.id,
        )
        
        return {"success": True, "count": count, "message": f"已禁止 {count} 个用户访问"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@kb_manage.post("/{kb_id}/access/allow")
async def allow_kb_access(
    kb_id: str,
    data: KBAccessAllow,
    current_user: User = Depends(get_superadmin_user),
):
    """允许用户访问知识库（从黑名单移除）"""
    service = KBAccessControlService()
    
    try:
        count = await service.allow_user_access(
            kb_id=kb_id,
            user_ids=data.user_ids,
        )
        
        return {"success": True, "count": count, "message": f"已允许 {count} 个用户访问"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@kb_manage.get("/{kb_id}/access")
async def get_kb_access_list(
    kb_id: str,
    current_user: User = Depends(get_admin_user),
):
    """获取知识库的访问控制列表"""
    service = KBAccessControlService()
    
    try:
        access_list = await service.get_kb_access_list(kb_id)
        return {"success": True, "data": access_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@kb_manage.get("/{kb_id}/check-access/{user_id}")
async def check_user_kb_access(
    kb_id: str,
    user_id: int,
    current_user: User = Depends(get_admin_user),
):
    """检查用户是否可以访问知识库"""
    service = KBAccessControlService()
    
    try:
        # 需要查询用户角色
        from src.storage.postgres.manager import pg_manager
        async with pg_manager.get_async_session_context() as session:
            from sqlalchemy import select
            from src.storage.postgres.models_business import User as UserModel
            
            result = await session.execute(
                select(UserModel.role).where(UserModel.id == user_id)
            )
            user = result.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            can_access = await service.can_user_access_kb(user_id, kb_id, user[0])
            
            return {
                "success": True,
                "can_access": can_access,
                "user_id": user_id,
                "kb_id": kb_id,
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


# =============================================================================
# === 知识库-智能体绑定路由 ===
# =============================================================================


@kb_manage.post("/{kb_id}/agent-bindings")
async def bind_kb_agents(
    kb_id: str,
    data: KBAgentBind,
    current_user: User = Depends(get_admin_user),
):
    """将知识库绑定到智能体"""
    service = KBAgentBindingService()
    count = await service.bind_agents(kb_id=kb_id, agent_ids=data.agent_ids, replace=data.replace)
    agents = await service.list_agents_for_kb(kb_id)
    return {"success": True, "count": count, "data": {"kb_id": kb_id, "agent_ids": agents}}


@kb_manage.get("/{kb_id}/agent-bindings")
async def list_kb_agents(
    kb_id: str,
    current_user: User = Depends(get_admin_user),
):
    """获取知识库绑定的智能体列表"""
    service = KBAgentBindingService()
    agents = await service.list_agents_for_kb(kb_id)
    return {"success": True, "data": {"kb_id": kb_id, "agent_ids": agents}}


@kb_manage.delete("/{kb_id}/agent-bindings/{agent_id}")
async def unbind_kb_agent(
    kb_id: str,
    agent_id: str,
    current_user: User = Depends(get_admin_user),
):
    """解除知识库与智能体的绑定"""
    service = KBAgentBindingService()
    await service.unbind_agent(kb_id=kb_id, agent_id=agent_id)
    agents = await service.list_agents_for_kb(kb_id)
    return {"success": True, "data": {"kb_id": kb_id, "agent_ids": agents}}
