<template>
  <div class="pr-page">
    <div class="pr-card">
      <div class="pr-head">
        <div class="pr-title">岗位职责清单</div>
        <div class="pr-subtitle">以岗位职责将管控措施落实到岗位，实现“事事有人管、人人都尽责”</div>
      </div>

      <div class="pr-filters">
        <a-input
          v-model:value="filters.keyword"
          placeholder="搜索岗位名称、职责…"
          class="pr-search"
          allow-clear
          @pressEnter="handleSearch"
        >
          <template #prefix>
            <Search size="16" style="color: var(--gray-400)" />
          </template>
        </a-input>
        <a-button type="primary" @click="handleSearch">搜索</a-button>
        <a-select v-model:value="filters.department" class="pr-select" placeholder="全部部门" allow-clear>
          <a-select-option value="合规管理部">合规管理部</a-select-option>
          <a-select-option value="物资部">物资部</a-select-option>
          <a-select-option value="建设部">建设部</a-select-option>
          <a-select-option value="财务部">财务部</a-select-option>
          <a-select-option value="安全部">安全部</a-select-option>
          <a-select-option value="营销部">营销部</a-select-option>
          <a-select-option value="人资部">人资部</a-select-option>
          <a-select-option value="法务部">法务部</a-select-option>
        </a-select>
      </div>

      <div class="pr-summary">共 {{ filteredList.length }} 条记录</div>

      <div class="pr-list">
        <div v-for="row in filteredList" :key="row.id" class="pr-item" @click="openDetail(row)">
          <div class="pr-item-main">
            <div class="pr-item-code">{{ row.code }}</div>
            <div class="pr-item-title">{{ row.title }}</div>
            <div class="pr-item-tags">
              <a-tag class="tag-dept">{{ row.department }}</a-tag>
              <a-tag class="tag-type">{{ row.complianceType }}</a-tag>
            </div>
          </div>
          <ChevronRight class="pr-arrow" size="18" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ChevronRight } from 'lucide-vue-next'

const router = useRouter()

const filters = ref({
  keyword: '',
  department: undefined
})

const list = ref([
  { id: 'GW-001', code: 'GW-001', title: '合规管理专员', department: '合规管理部', complianceType: '法律合规' },
  { id: 'GW-002', code: 'GW-002', title: '采购主管', department: '物资部', complianceType: '廉洁合规' },
  { id: 'GW-003', code: 'GW-003', title: '工程项目经理', department: '建设部', complianceType: '工程合规' },
  { id: 'GW-004', code: 'GW-004', title: '财务审核员', department: '财务部', complianceType: '财务合规' },
  { id: 'GW-005', code: 'GW-005', title: '安全监督员', department: '安全部', complianceType: '安全合规' },
  { id: 'GW-006', code: 'GW-006', title: '营销稽核员', department: '营销部', complianceType: '营销合规' },
  { id: 'GW-007', code: 'GW-007', title: '人力资源专员', department: '人资部', complianceType: '廉洁合规' },
  { id: 'GW-008', code: 'GW-008', title: '法律事务专员', department: '法务部', complianceType: '法律合规' }
])

const filteredList = computed(() => {
  const kw = (filters.value.keyword || '').trim()
  return list.value.filter((r) => {
    const hitKw = !kw || r.title.includes(kw) || r.department.includes(kw) || r.complianceType.includes(kw) || r.code.includes(kw)
    const hitDept = !filters.value.department || r.department === filters.value.department
    return hitKw && hitDept
  })
})

const handleSearch = () => {
  // 假数据，仅触发过滤
}

const openDetail = (row) => {
  router.push(`/compliance-risk/position-responsibility/${row.id}`)
}
</script>

<style scoped lang="less">
.pr-page {
  width: 100%;
}

.pr-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.pr-head {
  margin-bottom: 12px;
}

.pr-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-1000);
}

.pr-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.pr-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
}

.pr-search {
  flex: 1 1 380px;
  min-width: 260px;
  :deep(.ant-input-affix-wrapper) {
    border-radius: 10px;
  }
}

.pr-select {
  width: 130px;
}

.pr-summary {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--gray-100);
  font-size: 12px;
  color: var(--gray-600);
}

.pr-list {
  margin-top: 10px;
}

.pr-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 8px;
  border-bottom: 1px solid var(--gray-100);
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--gray-25);
    border-radius: 10px;
  }
}

.pr-item-code {
  font-size: 12px;
  font-weight: 700;
  color: var(--gray-600);
}

.pr-item-title {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--gray-1000);
}

.pr-item-tags {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-dept {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
  border: none;
}

.tag-type {
  background: rgba(59, 130, 246, 0.08);
  color: var(--gray-700);
  border: none;
}

.pr-arrow {
  color: var(--gray-400);
  flex: 0 0 auto;
  margin-top: 4px;
}
</style>

