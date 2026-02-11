<template>
  <div class="monitoring-config-view">
    <div class="page-header">
      <div class="header-left">
        <a-input
          v-model:value="searchText"
          placeholder="搜索域名、任务名"
          class="search-input"
          allow-clear
        />
        <a-select v-model:value="filterStatus" class="filter-select" placeholder="全部">
          <a-select-option value="all">全部</a-select-option>
          <a-select-option value="active">启用</a-select-option>
          <a-select-option value="inactive">禁用</a-select-option>
        </a-select>
      </div>
      <a-button type="primary" @click="handleAdd">
        <template #icon>
          <PlusOutlined />
        </template>
        新增监控网站
      </a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="tableData"
      :pagination="pagination"
      row-key="id"
      class="monitoring-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'target'">
          <div class="target-cell">
            <div class="target-name">{{ record.name }}</div>
            <div class="target-url">{{ record.url }}</div>
          </div>
        </template>
        <template v-else-if="column.key === 'frequency'">
          <div class="frequency-cell">
            <div class="frequency-type">{{ record.frequencyType }}</div>
            <div class="next-time">下一次 {{ record.nextTime }}</div>
          </div>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-switch v-model:checked="record.enabled" @change="handleStatusChange(record)" />
        </template>
        <template v-else-if="column.key === 'lastCollection'">
          <div class="last-collection-cell">
            <div class="collection-time">{{ record.lastCollectionTime }}</div>
            <div class="collection-result" :class="record.collectionStatus">
              {{ record.collectionResult }}
            </div>
          </div>
        </template>
        <template v-else-if="column.key === 'actions'">
          <div class="action-buttons">
            <a-button type="text" size="small" @click="handlePlay(record)" title="执行">
              ▶
            </a-button>
            <a-button type="text" size="small" @click="handleView(record)" title="查看">
              👁
            </a-button>
            <a-button type="text" size="small" @click="handleEdit(record)" title="编辑">
              ✏️
            </a-button>
            <a-button type="text" size="small" danger @click="handleDelete(record)" title="删除">
              🗑️
            </a-button>
          </div>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const searchText = ref('')
const filterStatus = ref('all')

const columns = [
  { title: '监控目标', key: 'target', width: '30%' },
  { title: '采集频率', key: 'frequency', width: '20%' },
  { title: '任务状态', key: 'status', width: '15%' },
  { title: '上次采集', key: 'lastCollection', width: '25%' },
  { title: '操作', key: 'actions', width: '10%' }
]

const tableData = ref([
  {
    id: 1,
    name: '国家能源局',
    url: 'http://www.nea.gov.cn/',
    frequencyType: 'Daily',
    nextTime: '14:00',
    enabled: true,
    lastCollectionTime: '2025.12.31 15:00',
    collectionStatus: 'success',
    collectionResult: '成功提取25条'
  },
  {
    id: 2,
    name: '信用中国',
    url: 'https://www.creditchina.gov.cn/',
    frequencyType: 'Daily',
    nextTime: '14:00',
    enabled: true,
    lastCollectionTime: '2025.12.31 15:00',
    collectionStatus: 'success',
    collectionResult: '成功提取25条'
  }
])

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: tableData.value.length
})

const handleAdd = () => {
  message.info('新增监控网站功能待实现')
}

const handleStatusChange = (record) => {
  message.success(`任务 ${record.name} 已${record.enabled ? '启用' : '禁用'}`)
}

const handlePlay = (record) => {
  message.info(`执行任务: ${record.name}`)
}

const handleView = (record) => {
  message.info(`查看任务: ${record.name}`)
}

const handleEdit = (record) => {
  message.info(`编辑任务: ${record.name}`)
}

const handleDelete = (record) => {
  message.warning(`删除任务: ${record.name}`)
}
</script>

<style lang="less" scoped>
.monitoring-config-view {
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

  .search-input {
    width: 300px;
  }

  .filter-select {
    width: 120px;
  }
}

.monitoring-table {
  :deep(.ant-table) {
    .target-cell {
      .target-name {
        font-weight: 500;
        color: #262626;
        margin-bottom: 4px;
      }
      .target-url {
        font-size: 12px;
        color: #8c8c8c;
      }
    }

    .frequency-cell {
      .frequency-type {
        color: #262626;
        margin-bottom: 4px;
      }
      .next-time {
        font-size: 12px;
        color: #8c8c8c;
      }
    }

    .last-collection-cell {
      .collection-time {
        color: #262626;
        margin-bottom: 4px;
      }
      .collection-result {
        font-size: 12px;
        &.success {
          color: #52c41a;
        }
        &.failed {
          color: #ff4d4f;
        }
      }
    }

    .action-buttons {
      display: flex;
      gap: 8px;
    }
  }
}
</style>