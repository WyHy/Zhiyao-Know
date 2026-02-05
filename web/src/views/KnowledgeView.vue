<template>
  <div class="knowledge-container layout-container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <div class="search-controls">
        <a-input
          v-model:value="searchParams.keyword"
          placeholder="搜索文件"
          size="large"
          class="search-input"
          allow-clear
          @pressEnter="handleSearch"
        >
          <template #prefix>
            <Search size="16" style="color: var(--gray-400)" />
          </template>
        </a-input>
        <a-tree-select
          v-model:value="searchParams.department_ids"
          placeholder="选择部门"
          size="large"
          :multiple="true"
          tree-checkable
          :tree-data="departmentTreeData"
          :maxTagCount="2"
          class="department-select"
          :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }"
          tree-default-expand-all
          show-checked-strategy="SHOW_ALL"
          allow-clear
          @change="handleDepartmentSelectChange"
        />
        <a-select
          v-model:value="searchParams.file_types"
          placeholder="文件类型"
          size="large"
          mode="multiple"
          class="file-type-select"
          :maxTagCount="2"
          allow-clear
        >
          <a-select-option value="pdf">PDF</a-select-option>
          <a-select-option value="word">Word</a-select-option>
          <a-select-option value="excel">Excel</a-select-option>
          <a-select-option value="ppt">PPT</a-select-option>
          <a-select-option value="jpg">JPG</a-select-option>
          <a-select-option value="png">PNG</a-select-option>
          <a-select-option value="txt">TXT</a-select-option>
          <a-select-option value="markdown">Markdown</a-select-option>
        </a-select>
        <a-select
          v-model:value="searchParams.sort_by"
          placeholder="排序方式"
          size="large"
          class="sort-select"
        >
          <a-select-option value="created_at">创建时间</a-select-option>
          <a-select-option value="updated_at">更新时间</a-select-option>
          <a-select-option value="filename">文件名</a-select-option>
          <a-select-option value="file_size">文件大小</a-select-option>
        </a-select>
        <a-button
          type="primary"
          size="large"
          @click="handleSearch"
          :loading="loading"
          class="search-btn"
        >
          <template #icon><Search size="16" /></template>
          搜索
        </a-button>
      </div>
    </div>

    <!-- 排序选项 -->
    <div class="sort-options">
      <a-checkbox v-model:checked="searchParams.include_subdepts">
        包含子部门
      </a-checkbox>
      <a-radio-group v-model:value="searchParams.order" class="order-radio-group">
        <a-radio-button value="desc">降序</a-radio-button>
        <a-radio-button value="asc">升序</a-radio-button>
      </a-radio-group>
    </div>

    <!-- 统计信息 -->
    <div class="summary-bar">
      共{{ pagination.total }}项 来自{{ departmentStatsCount }}个知识库 {{ departmentStatsCount }}个部门
    </div>

    <!-- 文件列表表格 -->
    <div class="file-list-container">
      <!-- 左侧部门树 -->
      <div class="department-tree-sidebar" :class="{ disabled: isMultiSelectMode }">
        <div class="sidebar-header">部门</div>
        <a-tree
          :tree-data="departmentTreeDataForTree"
          :selected-keys="selectedDepartmentKeys"
          :expanded-keys="expandedKeys"
          :block-node="true"
          @select="handleTreeSelect"
          @expand="handleTreeExpand"
          :disabled="isMultiSelectMode"
          class="department-tree"
        />
      </div>
      <!-- 右侧表格 -->
      <div class="table-wrapper">
        <a-table
          :columns="columns"
          :data-source="fileList"
          row-key="file_id"
          class="knowledge-table"
          size="small"
          :pagination="tablePagination"
          @change="handleTableChange"
          :loading="loading"
          :locale="{ emptyText: '暂无文件数据' }"
        >
        <template #bodyCell="{ column, record }">
          <div v-if="column.key === 'filename'">
            <a-button
              class="file-link-btn"
              type="link"
              @click="handleDownloadFile(record)"
            >
              <component
                :is="getFileIcon(record.filename)"
                :style="{
                  marginRight: '8px',
                  color: getFileIconColor(record.filename),
                  fontSize: '16px'
                }"
              />
              {{ record.filename }}
            </a-button>
          </div>
          <span v-else-if="column.key === 'size'">
            {{ record.size ? formatFileSize(record.size) : '-' }}
          </span>
          <div
            v-else-if="column.key === 'status'"
            style="display: flex; align-items: center; justify-content: center"
          >
            <a-tooltip :title="getStatusText(record.status)">
              <span
                v-if="record.status === 'done' || record.status === 'indexed'"
                style="color: var(--color-success-500)"
                ><CheckCircleFilled
              /></span>
              <span
                v-else-if="
                  record.status === 'failed' || record.status === 'error_parsing' || record.status === 'error_indexing'
                "
                style="color: var(--color-error-500)"
                ><CloseCircleFilled
              /></span>
              <span
                v-else-if="record.status === 'processing' || record.status === 'parsing' || record.status === 'indexing'"
                style="color: var(--color-info-500)"
                ><HourglassFilled
              /></span>
              <span
                v-else-if="record.status === 'waiting' || record.status === 'uploaded'"
                style="color: var(--color-warning-500)"
                ><ClockCircleFilled
              /></span>
              <span v-else-if="record.status === 'parsed'" style="color: var(--color-primary-500)"
                ><FileTextFilled
              /></span>
              <span v-else>{{ record.status }}</span>
            </a-tooltip>
          </div>
          <span v-else-if="column.key === 'created_at'">
            {{ record.created_at ? formatRelativeTime(record.created_at) : '-' }}
          </span>
          <div v-else-if="column.key === 'action'">
            <a-button
              type="link"
              size="small"
              @click="handleDownloadFile(record)"
              :disabled="
                record.status !== 'done' && record.status !== 'indexed' && record.status !== 'parsed' && record.status !== 'error_indexing'
              "
            >
              下载
            </a-button>
          </div>
        </template>
      </a-table>
      </div>
    </div>

    <!-- 文件详情弹窗 -->
    <FileDetailModal />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { message } from 'ant-design-vue'
import { Search } from 'lucide-vue-next'
import { apiGet } from '@/apis/base'
import { fileApi } from '@/apis/knowledge_api'
import { getFileIcon, getFileIconColor, formatFileSize, formatRelativeTime } from '@/utils/file_utils'
import FileDetailModal from '@/components/FileDetailModal.vue'
import {
  CheckCircleFilled,
  HourglassFilled,
  CloseCircleFilled,
  ClockCircleFilled,
  FileTextFilled
} from '@ant-design/icons-vue'
import { documentApi } from '@/apis/knowledge_api'

const userStore = useUserStore()

// 搜索参数（严格按照接口文档）
const searchParams = ref({
  keyword: '',
  department_ids: [],
  file_types: [],
  include_subdepts: true,
  order: 'desc',
  sort_by: 'created_at',
  page: 1,
  page_size: 20
})

// 部门列表（原始树形数据）
const departmentList = ref([])
// 部门树形数据（用于 TreeSelect）
const departmentTreeData = computed(() => {
  const transformData = (nodes) => {
    return nodes.map(node => ({
      title: node.name,
      value: node.id,
      key: node.id,
      children: node.children && node.children.length > 0 ? transformData(node.children) : undefined
    }))
  }
  return transformData(departmentList.value)
})
// 部门树形数据（用于左侧 Tree 组件）
const departmentTreeDataForTree = computed(() => {
  const transformData = (nodes) => {
    return nodes.map(node => ({
      title: node.name,
      key: node.id,
      value: node.id,
      children: node.children && node.children.length > 0 ? transformData(node.children) : undefined
    }))
  }
  return transformData(departmentList.value)
})
// 左侧树选中的部门（单选）
const selectedDepartmentKeys = ref([])
// 左侧树展开的节点
const expandedKeys = ref([])
// 是否是多选模式（上方下拉框选择了多个部门）
const isMultiSelectMode = computed(() => {
  return Array.isArray(searchParams.value.department_ids) && searchParams.value.department_ids.length > 1
})
const loading = ref(false)

// 文件列表和分页
const fileList = ref([])
const pagination = ref({
  total: 0,
  page: 1,
  page_size: 20
})

// 部门统计
const departmentStats = ref({})

// 计算部门统计数量
const departmentStatsCount = computed(() => {
  return Object.keys(departmentStats.value).length || 0
})

// 表格列定义
const columns = [
  {
    title: '文件名',
    dataIndex: 'filename',
    key: 'filename',
    ellipsis: true
  },
  {
    title: '大小',
    dataIndex: 'size',
    key: 'size',
    width: 100,
    align: 'right'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80,
    align: 'center'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 180,
    align: 'center'
  },
  {
    title: '操作',
    key: 'action',
    width: 80,
    align: 'center'
  }
]

// 表格分页配置
const tablePagination = computed(() => ({
  current: pagination.value.page,
  pageSize: pagination.value.page_size,
  total: pagination.value.total,
  showSizeChanger: true,
  showTotal: (total, range) => `共 ${total} 项，显示 ${range[0]}-${range[1]} 项`,
  pageSizeOptions: ['20', '50', '100'],
  hideOnSinglePage: false
}))

// 状态文本映射
const getStatusText = (status) => {
  const map = {
    uploaded: '已上传',
    parsing: '解析中',
    parsed: '已解析',
    error_parsing: '解析失败',
    indexing: '入库中',
    indexed: '已入库',
    error_indexing: '入库失败',
    done: '已入库',
    failed: '入库失败',
    processing: '处理中',
    waiting: '等待中'
  }
  return map[status] || status
}

// 加载部门列表（保持树形结构）
const loadDepartments = async () => {
  try {
    const response = await apiGet('/api/departments/tree', {}, true, 'json')
    console.log('部门接口响应:', response)
    
    // 处理响应格式：{ success: true, data: [...] }
    let list = []
    if (response && response.success && Array.isArray(response.data)) {
      list = response.data
    } else if (Array.isArray(response)) {
      list = response
    } else if (response && Array.isArray(response.data)) {
      list = response.data
    }
    
    // 保持树形结构
    departmentList.value = list
    
    // 如果用户有部门ID，设置为默认选中值并展开
    if (userStore.departmentId && searchParams.value.department_ids.length === 0) {
      searchParams.value.department_ids = [userStore.departmentId]
      selectedDepartmentKeys.value = [userStore.departmentId]
      // 延迟展开，确保树数据已加载
      setTimeout(() => {
        expandToNode(userStore.departmentId)
      }, 100)
    }
    
    console.log('处理后的部门列表:', departmentList.value)
  } catch (error) {
    console.error('加载部门列表失败:', error)
    // 如果加载失败，至少显示当前用户的部门
    if (userStore.departmentId && userStore.departmentName) {
      departmentList.value = [{
        id: userStore.departmentId,
        name: userStore.departmentName,
        children: []
      }]
      // 设置默认选中值并展开
      if (searchParams.value.department_ids.length === 0) {
        searchParams.value.department_ids = [userStore.departmentId]
        selectedDepartmentKeys.value = [userStore.departmentId]
        // 延迟展开，确保树数据已加载
        setTimeout(() => {
          expandToNode(userStore.departmentId)
        }, 100)
      }
    }
  }
}

// 搜索文件
const handleSearch = async () => {
  loading.value = true
  try {
    // 构建请求参数（严格按照接口文档）
    const params = {
      department_ids: searchParams.value.department_ids || [],
      file_types: searchParams.value.file_types || [],
      include_subdepts: searchParams.value.include_subdepts,
      keyword: searchParams.value.keyword || '',
      order: searchParams.value.order,
      page: searchParams.value.page,
      page_size: searchParams.value.page_size,
      sort_by: searchParams.value.sort_by
    }

    console.log('搜索参数:', params)

    const response = await fileApi.searchFiles(params)
    
    console.log('搜索响应:', response)
    
    if (response.success && response.data) {
      fileList.value = response.data.files || []
      pagination.value = {
        total: response.data.total || 0,
        page: response.data.page || 1,
        page_size: response.data.page_size || 20
      }
      departmentStats.value = response.data.department_stats || {}
    } else {
      message.error('搜索失败')
      fileList.value = []
      pagination.value = {
        total: 0,
        page: 1,
        page_size: 20
      }
      departmentStats.value = {}
    }
  } catch (error) {
    console.error('搜索文件失败:', error)
    message.error(error.message || '搜索文件失败')
    fileList.value = []
    pagination.value = {
      total: 0,
      page: 1,
      page_size: 20
    }
    departmentStats.value = {}
  } finally {
    loading.value = false
  }
}

// 表格分页变化
const handleTableChange = (pag) => {
  searchParams.value.page = pag.current
  searchParams.value.page_size = pag.pageSize
  handleSearch()
}

// 查找节点的所有父节点ID
const findParentKeys = (treeData, targetId, parentKeys = []) => {
  for (const node of treeData) {
    if (node.key === targetId) {
      return parentKeys
    }
    if (node.children && node.children.length > 0) {
      const found = findParentKeys(node.children, targetId, [...parentKeys, node.key])
      if (found !== null) {
        return found
      }
    }
  }
  return null
}

// 展开到指定节点
const expandToNode = (nodeId) => {
  const parentKeys = findParentKeys(departmentTreeDataForTree.value, nodeId)
  if (parentKeys) {
    expandedKeys.value = [...new Set([...expandedKeys.value, ...parentKeys])]
  }
}

// 处理左侧树展开
const handleTreeExpand = (keys) => {
  expandedKeys.value = keys
}

// 处理左侧树选择（单选）
const handleTreeSelect = (selectedKeys) => {
  if (isMultiSelectMode.value) {
    // 多选模式下，左侧树被禁用，不处理选择
    return
  }
  
  if (selectedKeys && selectedKeys.length > 0) {
    const selectedId = selectedKeys[0]
    selectedDepartmentKeys.value = selectedKeys
    // 展开到选中的节点
    expandToNode(selectedId)
    // 更新上方下拉框为单选模式
    searchParams.value.department_ids = [selectedId]
    // 触发搜索
    handleSearch()
  } else {
    selectedDepartmentKeys.value = []
    searchParams.value.department_ids = []
  }
}

// 处理上方下拉框变化
const handleDepartmentSelectChange = (value) => {
  // 如果选择了多个部门，清空左侧树的选中状态
  if (Array.isArray(value) && value.length > 1) {
    selectedDepartmentKeys.value = []
    expandedKeys.value = []
    // 多选时也执行搜索
    handleSearch()
  } else if (Array.isArray(value) && value.length === 1) {
    // 如果只选择了一个部门，更新左侧树的选中状态并展开，然后执行搜索
    selectedDepartmentKeys.value = [value[0]]
    expandToNode(value[0])
    // 执行搜索
    handleSearch()
  } else {
    selectedDepartmentKeys.value = []
    expandedKeys.value = []
    // 清空时也执行搜索
    handleSearch()
  }
}

// 下载文件
const handleDownloadFile = async (record) => {
  try {
    // 如果文件有 db_id 和 file_id，使用现有的下载接口
    if (record.db_id && record.file_id) {
      const response = await documentApi.downloadDocument(record.db_id, record.file_id)

      const contentDisposition = response.headers.get('content-disposition')
      let filename = record.filename
      if (contentDisposition) {
        const rfc2231Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/)
        if (rfc2231Match) {
          try {
            filename = decodeURIComponent(rfc2231Match[1])
          } catch (error) {
            console.warn('Failed to decode RFC2231 filename:', rfc2231Match[1], error)
          }
        } else {
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].replace(/['"]/g, '')
            try {
              filename = decodeURIComponent(filename)
            } catch (error) {
              console.warn('Failed to decode filename:', filename, error)
            }
          }
        }
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success('下载成功')
    } else {
      message.warning('文件信息不完整，无法下载')
    }
  } catch (error) {
    console.error('下载文件时出错:', error)
    message.error(error.message || '下载文件失败')
  }
}

onMounted(async () => {
  // 确保用户信息已加载
  if (userStore.token && !userStore.departmentId) {
    try {
      await userStore.getCurrentUser()
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
  
  await loadDepartments()
  
  // 初始化时同步左侧树选中状态并展开
  if (Array.isArray(searchParams.value.department_ids) && searchParams.value.department_ids.length === 1) {
    selectedDepartmentKeys.value = [searchParams.value.department_ids[0]]
    expandToNode(searchParams.value.department_ids[0])
  }
  
  // 默认加载一次
  await handleSearch()
})
</script>

<style lang="less" scoped>
.knowledge-container {
  height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 16px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  box-sizing: border-box;
}

.search-bar {
  flex-shrink: 0;
  padding: 16px 0;
  border-bottom: 1px solid var(--gray-100);
}

.search-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 140px;
  max-width: 240px;

  :deep(.ant-input-affix-wrapper) {
    display: flex;
    align-items: center;
  }

  :deep(.ant-input-prefix) {
    display: flex;
    align-items: center;
    margin-right: 8px;
  }

  :deep(.ant-input) {
    line-height: 1.5715;
  }
}

.department-select {
  flex: 1;
  min-width: 140px;
  max-width: 240px;
}

.file-type-select,
.file-size-select,
.sort-select {
  width: 150px;
}

.search-btn {
  height: 40px;
  padding: 0 24px;
}

.sort-options {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--gray-100);
}

.order-radio-group {
  margin-left: auto;
}

.summary-bar {
  flex-shrink: 0;
  padding: 12px 0;
  color: var(--gray-600);
  font-size: 14px;
  border-bottom: 1px solid var(--gray-100);
}

.file-list-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: row;
  margin-top: 16px;
  gap: 16px;
}

.department-tree-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--gray-50);
  border-radius: 8px;
  padding: 16px 8px 16px 16px;
  overflow-y: auto;
  border: 1px solid var(--gray-150);
  transition: all 0.3s ease;

  &.disabled {
    opacity: 0.6;
    pointer-events: none;
    background: var(--gray-100);
    
    .sidebar-header {
      color: var(--gray-400);
    }
    
    :deep(.ant-tree-title) {
      color: var(--gray-400) !important;
    }
    
    :deep(.ant-tree-node-content-wrapper) {
      color: var(--gray-400) !important;
    }
  }

  .sidebar-header {
    font-size: 14px;
    font-weight: 600;
    color: var(--gray-900);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--gray-200);
  }

  .department-tree {
    :deep(.ant-tree-list),
    :deep(ul.ant-tree-list) {
      padding: 8px 8px 8px 0 !important;
      margin-right: 8px !important;
    }
    
    :deep(.ant-tree-list-holder) {
      padding: 8px 8px 8px 0 !important;
    }
    
    :deep(.ant-tree-list-holder-inner) {
      padding: 8px 8px 8px 0 !important;
    }
    
    :deep(.ant-tree) {
      padding: 8px 8px 8px 0 !important;
    }

    :deep(.ant-tree-node-selected) {
      background-color: var(--main-5);
    }

    :deep(.ant-tree-node-content-wrapper) {
      border-radius: 4px;
      padding: 4px 8px;
      padding-right: 16px;
      margin-right: 10px;
      transition: all 0.2s ease;

      &:hover {
        background-color: var(--gray-100);
      }
    }

    :deep(.ant-tree-node-selected .ant-tree-node-content-wrapper) {
      background-color: var(--main-5);
      color: var(--main-color);
      padding-right: 16px;
      margin-right: 10px;
    }

    :deep(.ant-tree-node-content-wrapper:hover) {
      background-color: var(--gray-100);
    }

    :deep(.ant-tree-title) {
      color: var(--gray-900);
      font-size: 14px;
    }

    :deep(.ant-tree-treenode) {
      margin-bottom: 2px;
    }
  }
}

.table-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.knowledge-table {
  flex: 1;
  overflow: auto;
  background-color: transparent;
}

.file-link-btn {
  padding: 0;
  height: auto;
  line-height: 1.4;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  display: flex;
  align-items: center;
}

.file-link-btn:hover {
  color: var(--main-color);
}

:deep(.ant-table-wrapper) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.ant-table) {
  flex: 1;
  overflow: auto;
}

:deep(.ant-table-container) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.ant-table-content) {
  flex: 1;
  overflow: auto;
}

:deep(.ant-table-thead > tr > th) {
  background-color: var(--gray-50);
  font-weight: 500;
  color: var(--gray-700);
  padding: 10px 16px;
  border-bottom: 1px solid var(--gray-150);
}

:deep(.ant-table-tbody > tr > td) {
  padding: 10px 16px;
  border-bottom: 1px solid var(--gray-100);
  color: var(--gray-800);
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: var(--main-5);
}
</style>
