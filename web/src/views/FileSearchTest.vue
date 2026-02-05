<template>
  <div class="file-search-test-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>文件检索测试</h2>
      <p class="description">测试按部门和关键词检索知识库文件的功能</p>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="search-section">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input
            v-model:value="searchParams.keyword"
            placeholder="搜索文件名"
            allow-clear
            @pressEnter="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
        <a-col :span="6">
          <a-tree-select
            v-model:value="searchParams.department_ids"
            :tree-data="departmentTreeData"
            placeholder="选择部门"
            multiple
            allow-clear
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
            tree-checkable
            show-checked-strategy="SHOW_PARENT"
            style="width: 100%"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="searchParams.file_types"
            mode="multiple"
            placeholder="文件类型"
            allow-clear
            style="width: 100%"
          >
            <a-select-option value="pdf">PDF</a-select-option>
            <a-select-option value="docx">Word</a-select-option>
            <a-select-option value="xlsx">Excel</a-select-option>
            <a-select-option value="pptx">PPT</a-select-option>
            <a-select-option value="jpg">JPG</a-select-option>
            <a-select-option value="png">PNG</a-select-option>
            <a-select-option value="txt">TXT</a-select-option>
            <a-select-option value="md">Markdown</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select
            v-model:value="searchParams.sort_by"
            style="width: 100%"
          >
            <a-select-option value="created_at">创建时间</a-select-option>
            <a-select-option value="updated_at">更新时间</a-select-option>
            <a-select-option value="filename">文件名</a-select-option>
            <a-select-option value="file_size">文件大小</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-button type="primary" @click="handleSearch" :loading="loading">
            <SearchOutlined />
            搜索
          </a-button>
        </a-col>
      </a-row>

      <!-- 高级选项 -->
      <div class="advanced-options" style="margin-top: 12px">
        <a-checkbox v-model:checked="searchParams.include_subdepts">
          包含子部门
        </a-checkbox>
        <a-radio-group v-model:value="searchParams.order" style="margin-left: 24px">
          <a-radio value="desc">降序</a-radio>
          <a-radio value="asc">升序</a-radio>
        </a-radio-group>
      </div>
    </div>

    <!-- 结果统计 -->
    <div class="result-stats" v-if="searchResult">
      <a-space>
        <span>共 {{ searchResult.total }} 项</span>
        <a-divider type="vertical" />
        <span>来自 {{ searchResult.kb_count }} 个知识库</span>
        <a-divider type="vertical" />
        <span>{{ searchResult.dept_count }} 个部门</span>
      </a-space>
    </div>

    <!-- 文件列表 -->
    <div class="file-list-section">
      <a-spin :spinning="loading">
        <a-table
          :dataSource="fileList"
          :columns="columns"
          :pagination="pagination"
          :rowKey="(record) => record.file_id"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <!-- 文件名列 -->
            <template v-if="column.key === 'filename'">
              <div class="file-name-cell">
                <FileIcon :filename="record.filename" />
                <span class="filename-text">{{ record.filename }}</span>
              </div>
            </template>

            <!-- 知识库列 -->
            <template v-if="column.key === 'kb_name'">
              <a-tag color="blue">{{ record.kb_name }}</a-tag>
            </template>

            <!-- 部门列 -->
            <template v-if="column.key === 'department_names'">
              <a-space wrap>
                <a-tag
                  v-for="dept in record.department_names"
                  :key="dept"
                  color="green"
                >
                  {{ dept }}
                </a-tag>
              </a-space>
            </template>

            <!-- 文件大小列 -->
            <template v-if="column.key === 'file_size'">
              {{ formatFileSize(record.file_size) }}
            </template>

            <!-- 状态列 -->
            <template v-if="column.key === 'status'">
              <a-badge
                :status="getStatusBadge(record.status)"
                :text="getStatusText(record.status)"
              />
            </template>

            <!-- 创建时间列 -->
            <template v-if="column.key === 'created_at'">
              {{ formatTime(record.created_at) }}
            </template>

            <!-- 操作列 -->
            <template v-if="column.key === 'action'">
              <a-space>
                <a-tooltip title="查看详情">
                  <a-button type="link" size="small" @click="handleView(record)">
                    <EyeOutlined />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="下载">
                  <a-button type="link" size="small" @click="handleDownload(record)">
                    <DownloadOutlined />
                  </a-button>
                </a-tooltip>
              </a-space>
            </template>
          </template>

          <template #emptyText>
            <a-empty description="暂无文件数据" />
          </template>
        </a-table>
      </a-spin>
    </div>

    <!-- 文件详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="文件详情"
      width="600px"
      :footer="null"
    >
      <div v-if="selectedFile" class="file-detail">
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="文件名">
            {{ selectedFile.filename }}
          </a-descriptions-item>
          <a-descriptions-item label="文件ID">
            {{ selectedFile.file_id }}
          </a-descriptions-item>
          <a-descriptions-item label="知识库">
            <a-tag color="blue">{{ selectedFile.kb_name }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="所属部门">
            <a-space wrap>
              <a-tag
                v-for="dept in selectedFile.department_names"
                :key="dept"
                color="green"
              >
                {{ dept }}
              </a-tag>
            </a-space>
          </a-descriptions-item>
          <a-descriptions-item label="文件大小">
            {{ formatFileSize(selectedFile.file_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="文件类型">
            {{ selectedFile.file_type }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-badge
              :status="getStatusBadge(selectedFile.status)"
              :text="getStatusText(selectedFile.status)"
            />
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatTime(selectedFile.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="更新时间">
            {{ formatTime(selectedFile.updated_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="标题" v-if="selectedFile.title">
            {{ selectedFile.title }}
          </a-descriptions-item>
          <a-descriptions-item label="摘要" v-if="selectedFile.summary">
            {{ selectedFile.summary }}
          </a-descriptions-item>
          <a-descriptions-item label="标签" v-if="selectedFile.tags?.length">
            <a-space wrap>
              <a-tag v-for="tag in selectedFile.tags" :key="tag">{{ tag }}</a-tag>
            </a-space>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { notification } from 'ant-design-vue'
import {
  SearchOutlined,
  DownloadOutlined,
  EyeOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileImageOutlined,
  FileOutlined
} from '@ant-design/icons-vue'
import { searchFiles } from '@/apis/fileSearch'
import { getDepartments } from '@/apis/department_api'

// 搜索参数
const searchParams = reactive({
  keyword: '',
  department_ids: [],
  include_subdepts: true,
  file_types: [],
  sort_by: 'created_at',
  order: 'desc',
  page: 1,
  page_size: 20
})

// 数据状态
const loading = ref(false)
const fileList = ref([])
const searchResult = ref(null)
const selectedFile = ref(null)
const detailModalVisible = ref(false)

// 部门数据
const departmentManagement = reactive({
  departmentTree: [],
  loading: false
})

// 表格列定义
const columns = [
  {
    title: '文件名',
    key: 'filename',
    width: 280,
    ellipsis: true
  },
  {
    title: '知识库',
    key: 'kb_name',
    width: 150
  },
  {
    title: '部门',
    key: 'department_names',
    width: 200
  },
  {
    title: '大小',
    key: 'file_size',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160
  },
  {
    title: '操作',
    key: 'action',
    width: 120,
    align: 'center',
    fixed: 'right'
  }
]

// 分页配置
const pagination = computed(() => ({
  current: searchParams.page,
  pageSize: searchParams.page_size,
  total: searchResult.value?.total || 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 项`
}))

// 部门树数据
const departmentTreeData = computed(() => {
  return departmentManagement.departmentTree
})

// 文件图标组件
const FileIcon = ({ filename }) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    pdf: FilePdfOutlined,
    doc: FileWordOutlined,
    docx: FileWordOutlined,
    xls: FileExcelOutlined,
    xlsx: FileExcelOutlined,
    ppt: FilePptOutlined,
    pptx: FilePptOutlined,
    jpg: FileImageOutlined,
    jpeg: FileImageOutlined,
    png: FileImageOutlined,
    gif: FileImageOutlined,
    txt: FileTextOutlined,
    md: FileTextOutlined
  }
  const IconComponent = iconMap[ext] || FileOutlined
  return h(IconComponent, { style: { fontSize: '18px', marginRight: '8px' } })
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  // 3天内显示相对时间
  if (diff < 3 * 24 * 60 * 60 * 1000) {
    if (diff < 60 * 1000) return '刚刚'
    if (diff < 60 * 60 * 1000) return `${Math.floor(diff / (60 * 1000))} 分钟前`
    if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / (60 * 60 * 1000))} 小时前`
    return `${Math.floor(diff / (24 * 60 * 60 * 1000))} 天前`
  }

  // 超过3天显示具体日期
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取状态徽章
const getStatusBadge = (status) => {
  const statusMap = {
    uploaded: 'processing',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return statusMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    uploaded: '已上传',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

// 搜索文件
const handleSearch = async () => {
  loading.value = true
  try {
    const response = await searchFiles(searchParams)
    
    if (response.success) {
      searchResult.value = response.data
      fileList.value = response.data.files || []
      
      notification.success({
        message: '搜索成功',
        description: `找到 ${response.data.total} 个文件`
      })
    }
  } catch (error) {
    console.error('搜索失败:', error)
    notification.error({
      message: '搜索失败',
      description: error.message || '请稍后重试'
    })
  } finally {
    loading.value = false
  }
}

// 表格变化处理
const handleTableChange = (paginationConfig, filters, sorter) => {
  searchParams.page = paginationConfig.current
  searchParams.page_size = paginationConfig.pageSize
  handleSearch()
}

// 查看详情
const handleView = (file) => {
  selectedFile.value = file
  detailModalVisible.value = true
}

// 下载文件
const handleDownload = (file) => {
  notification.info({
    message: '下载功能',
    description: `准备下载: ${file.filename}`
  })
  // TODO: 实现下载逻辑
}

// 获取部门树
const fetchDepartments = async () => {
  departmentManagement.loading = true
  try {
    const response = await getDepartments()
    if (response.success) {
      departmentManagement.departmentTree = response.data || []
    }
  } catch (error) {
    console.error('获取部门列表失败:', error)
    notification.error({
      message: '获取部门失败',
      description: error.message || '请稍后重试'
    })
  } finally {
    departmentManagement.loading = false
  }
}

// 组件挂载
onMounted(async () => {
  await fetchDepartments()
  await handleSearch()
})
</script>

<style lang="less" scoped>
.file-search-test-page {
  padding: 24px;
  background: var(--gray-0);
  min-height: 100vh;

  .page-header {
    margin-bottom: 24px;

    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--gray-900);
    }

    .description {
      margin: 8px 0 0;
      font-size: 14px;
      color: var(--gray-600);
    }
  }

  .search-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    margin-bottom: 16px;

    .advanced-options {
      padding-top: 12px;
      border-top: 1px solid var(--gray-150);
    }
  }

  .result-stats {
    padding: 12px 20px;
    background: var(--gray-25);
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 14px;
    color: var(--gray-700);
  }

  .file-list-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    :deep(.ant-table) {
      .file-name-cell {
        display: flex;
        align-items: center;

        .filename-text {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .file-detail {
    :deep(.ant-descriptions-item-label) {
      width: 120px;
      font-weight: 500;
    }
  }
}
</style>
