<template>
  <div class="log-management-view">
    <div class="page-header">
      <div class="header-left">
        <a-range-picker v-model:value="dateRange" class="date-picker" />
        <a-select v-model:value="filterStatus" class="filter-select" placeholder="全部状态">
          <a-select-option value="all">全部状态</a-select-option>
          <a-select-option value="success">成功</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>
      </div>
      <a-button type="primary" @click="handleExport">
        <template #icon>
          <span>📥</span>
        </template>
        导出CSV
      </a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="tableData"
      :pagination="pagination"
      row-key="id"
      class="log-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <div class="status-cell">
            <span class="status-dot" :class="record.status"></span>
            <span>{{ record.statusText }}</span>
          </div>
        </template>
        <template v-else-if="column.key === 'dataVolume'">
          <a-button v-if="record.dataVolume" type="link" size="small">
            {{ record.dataVolume }} items
          </a-button>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from '@/utils/time'

const dateRange = ref(null)
const filterStatus = ref('all')

const columns = [
  { title: '执行时间', dataIndex: 'executionTime', key: 'executionTime', width: '20%' },
  { title: '所属任务', dataIndex: 'taskName', key: 'taskName', width: '20%' },
  { title: '状态', key: 'status', width: '15%' },
  { title: '系统日志详情', dataIndex: 'logDetail', key: 'logDetail', width: '30%' },
  { title: '数据量', key: 'dataVolume', width: '15%' }
]

const tableData = ref([
  {
    id: 1,
    executionTime: '2025-12-31 15:00:04',
    taskName: '国家发改委爬取',
    status: 'failed',
    statusText: '失败',
    logDetail: '提取失败:403 Forbidden',
    dataVolume: null
  },
  {
    id: 2,
    executionTime: '2025-12-31 15:00:04',
    taskName: '国家发改委爬取',
    status: 'success',
    statusText: '成功',
    logDetail: '提取成功:已识别出5条项目',
    dataVolume: '5 items'
  },
  {
    id: 3,
    executionTime: '2025-12-31 15:00:04',
    taskName: '湖北省电力爬取',
    status: 'success',
    statusText: '成功',
    logDetail: '提取成功:已识别出7条项目',
    dataVolume: '7 items'
  }
])

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 3,
  showSizeChanger: false,
  showQuickJumper: true
})

const handleExport = () => {
  message.info('导出CSV功能待实现')
}
</script>

<style lang="less" scoped>
.log-management-view {
  padding: 24px;
  background: #ffffff;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
    display: flex;
    gap: 12px;
  }

  .date-picker {
    width: 300px;
  }

  .filter-select {
    width: 150px;
  }
}

.log-table {
  :deep(.ant-table) {
    .status-cell {
      display: flex;
      align-items: center;
      gap: 8px;

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.success {
          background: #52c41a;
        }

        &.failed {
          background: #ff4d4f;
        }
      }
    }
  }
}
</style>