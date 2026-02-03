/**
 * 部门管理 API
 */

import {
  apiAdminGet,
  apiSuperAdminGet,
  apiSuperAdminPost,
  apiSuperAdminPut,
  apiSuperAdminDelete
} from './base'

const BASE_URL = '/api/departments'

/**
 * 获取部门列表（普通管理员可访问）
 * @returns {Promise<Object>} 部门列表响应 { success: true, data: [...] }
 */
export const getDepartments = async () => {
  const response = await apiAdminGet(`${BASE_URL}/tree`)
  // 处理响应格式：{ success: true, data: [...] }
  if (response && response.success && Array.isArray(response.data)) {
    return response.data
  }
  // 兼容旧格式：直接返回数组
  if (Array.isArray(response)) {
    return response
  }
  return []
}

/**
 * 获取部门详情
 * @param {number} departmentId - 部门ID
 * @returns {Promise<Object>} 部门详情
 */
export const getDepartment = (departmentId) => {
  return apiSuperAdminGet(`${BASE_URL}/${departmentId}`)
}

/**
 * 创建部门
 * @param {Object} data - 部门数据
 * @param {string} data.name - 部门名称
 * @param {string} [data.description] - 部门描述
 * @param {number} [data.parent_id] - 上级部门ID，null 则为顶级部门
 * @param {number} [data.sort_order] - 排序顺序，默认 0
 * @returns {Promise<Object>} 创建的部门
 */
export const createDepartment = (data) => {
  return apiSuperAdminPost(BASE_URL, data)
}

/**
 * 更新部门
 * @param {number} departmentId - 部门ID
 * @param {Object} data - 部门数据
 * @param {string} [data.name] - 部门名称
 * @param {string} [data.description] - 部门描述
 * @returns {Promise<Object>} 更新后的部门
 */
export const updateDepartment = (departmentId, data) => {
  return apiSuperAdminPut(`${BASE_URL}/${departmentId}`, data)
}

/**
 * 删除部门
 * @param {number} departmentId - 部门ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteDepartment = (departmentId) => {
  return apiSuperAdminDelete(`${BASE_URL}/${departmentId}`)
}

export const departmentApi = {
  getDepartments,
  getDepartment,
  createDepartment,
  updateDepartment,
  deleteDepartment
}
