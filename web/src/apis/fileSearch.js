/**
 * 文件检索 API
 */

import { apiAdminGet, apiAdminPost } from './base'

/**
 * 搜索文件（POST）
 * @param {Object} params 搜索参数
 * @param {Array<number>} params.department_ids 部门ID列表
 * @param {boolean} params.include_subdepts 是否包含子部门
 * @param {string} params.keyword 关键词
 * @param {Array<string>} params.file_types 文件类型列表
 * @param {string} params.date_from 开始时间
 * @param {string} params.date_to 结束时间
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @param {string} params.sort_by 排序字段
 * @param {string} params.order 排序顺序
 * @returns {Promise}
 */
export function searchFiles(params) {
  return apiAdminPost('/api/files/search', params)
}

/**
 * 搜索文件（GET）
 * @param {Object} params 搜索参数
 * @returns {Promise}
 */
export function searchFilesGet(params) {
  // 将数组参数转换为逗号分隔的字符串
  const queryParams = { ...params }
  if (queryParams.department_ids && Array.isArray(queryParams.department_ids)) {
    queryParams.department_ids = queryParams.department_ids.join(',')
  }
  if (queryParams.file_types && Array.isArray(queryParams.file_types)) {
    queryParams.file_types = queryParams.file_types.join(',')
  }

  const queryString = new URLSearchParams(queryParams).toString()
  return apiAdminGet(`/api/files/search?${queryString}`)
}

/**
 * 获取文件统计信息
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getFileStats(params) {
  const queryString = new URLSearchParams(params).toString()
  return apiAdminGet(`/api/files/stats?${queryString}`)
}
