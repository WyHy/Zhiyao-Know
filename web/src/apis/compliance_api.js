import { apiAdminGet, apiAdminPost } from './base'

function buildQuery(params = {}) {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      searchParams.set(key, String(value))
    }
  })
  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

export const complianceApi = {
  importExcel: async (dataType, file, replaceExisting = true) => {
    const formData = new FormData()
    formData.append('data_type', dataType)
    formData.append('replace_existing', String(replaceExisting))
    formData.append('file', file)
    return apiAdminPost('/api/compliance-risk/import/excel', formData)
  },

  getSummary: async () => apiAdminGet('/api/compliance-risk/summary'),

  getRiskLibrary: async (params = {}) => apiAdminGet(`/api/compliance-risk/risk-library${buildQuery(params)}`),
  getRiskLibraryDetail: async (id) => apiAdminGet(`/api/compliance-risk/risk-library/${id}`),

  getProcessChecklist: async (params = {}) =>
    apiAdminGet(`/api/compliance-risk/process-checklist${buildQuery(params)}`),
  getProcessChecklistDetail: async (id) => apiAdminGet(`/api/compliance-risk/process-checklist/${id}`),

  getPositionResponsibility: async (params = {}) =>
    apiAdminGet(`/api/compliance-risk/position-responsibility${buildQuery(params)}`),
  getPositionResponsibilityDetail: async (id) => apiAdminGet(`/api/compliance-risk/position-responsibility/${id}`)
}
