<template>
  <div class="rl-page">
    <div class="rl-card">
      <div class="rl-head">
        <div class="rl-title">合规风险库</div>
        <div class="rl-subtitle">合规管理工作基础，对工作中的合规风险点进行系统梳理和分级管控</div>
      </div>

      <div class="rl-filters">
        <a-input
          v-model:value="filters.keyword"
          placeholder="搜索风险描述、业务类型…"
          class="rl-search"
          allow-clear
          @pressEnter="handleSearch"
        >
          <template #prefix>
            <Search size="16" style="color: var(--gray-400)" />
          </template>
        </a-input>
        <a-button type="primary" @click="handleSearch">搜索</a-button>
        <a-select v-model:value="filters.level" class="rl-select" placeholder="全部等级" allow-clear>
          <a-select-option value="高风险">高风险</a-select-option>
          <a-select-option value="中风险">中风险</a-select-option>
          <a-select-option value="低风险">低风险</a-select-option>
        </a-select>
        <a-select v-model:value="filters.department" class="rl-select" placeholder="全部部门" allow-clear>
          <a-select-option value="物资部">物资部</a-select-option>
          <a-select-option value="财务部">财务部</a-select-option>
          <a-select-option value="法务部">法务部</a-select-option>
          <a-select-option value="安全部">安全部</a-select-option>
          <a-select-option value="营销部">营销部</a-select-option>
          <a-select-option value="信息部">信息部</a-select-option>
        </a-select>
      </div>

      <div class="rl-summary">共 {{ filteredList.length }} 条记录</div>

      <div class="rl-list">
        <div v-for="row in filteredList" :key="row.id" class="rl-item" @click="openDetail(row)">
          <div class="rl-item-main">
            <div class="rl-item-top">
              <a-tag :color="row.levelColor" class="rl-tag">{{ row.level }}</a-tag>
              <a-tag color="blue" class="rl-tag">{{ row.category }}</a-tag>
            </div>
            <div class="rl-item-title">{{ row.title }}</div>
            <div class="rl-item-desc">{{ row.desc }}</div>
            <div class="rl-item-chips">
              <a-tag v-for="chip in row.chips" :key="chip" class="rl-chip">{{ chip }}</a-tag>
            </div>
          </div>

          <div class="rl-item-side">
            <a-tag color="blue" class="rl-code">{{ row.code }}</a-tag>
            <ChevronRight class="rl-arrow" size="18" />
          </div>
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
  level: undefined,
  department: undefined
})

const list = ref([
  {
    id: 'FX-001',
    code: 'FX-001',
    level: '高风险',
    levelColor: 'red',
    category: '法律合规',
    title: '招标采购立项',
    desc: '未按规定履行招标程序，存在规避招标、化整为零规避招标等违规行为',
    chips: ['招标采购', '采购项目立项', '物资部'],
    department: '物资部'
  },
  {
    id: 'FX-002',
    code: 'FX-002',
    level: '高风险',
    levelColor: 'red',
    category: '工程合规',
    title: '工程违规转包、分包',
    desc: '工程违规转包、分包，导致工程质量风险，违反合同约定及法律规定',
    chips: ['工程建设', '工程分包管理', '建设部'],
    department: '建设部'
  },
  {
    id: 'FX-003',
    code: 'FX-003',
    level: '中风险',
    levelColor: 'orange',
    category: '财务合规',
    title: '超预算/超额度支出',
    desc: '未按规定走审批，擅自调整预算或超额支出，存在财务违规风险',
    chips: ['财务管理', '预算执行', '财务部'],
    department: '财务部'
  },
  {
    id: 'FX-004',
    code: 'FX-004',
    level: '高风险',
    levelColor: 'red',
    category: '安全合规',
    title: '作业现场违规',
    desc: '作业人员未按规定佩戴安全防护用品，存在人身伤亡事故风险',
    chips: ['安全生产', '作业现场管控', '安全部'],
    department: '安全部'
  },
  {
    id: 'FX-005',
    code: 'FX-005',
    level: '中风险',
    levelColor: 'orange',
    category: '营销合规',
    title: '异常电费处理',
    desc: '电费计量装置异常未及时发现处理，造成电费损失，影响营业收入',
    chips: ['营销服务', '电费抄核收', '营销部'],
    department: '营销部'
  },
  {
    id: 'FX-006',
    code: 'FX-006',
    level: '高风险',
    levelColor: 'red',
    category: '廉洁合规',
    title: '招投标过程违规操作',
    desc: '招投标过程中存在暗箱操作、违反公平竞争原则，存在廉洁风险',
    chips: ['人力资源', '招投管理', '人资部'],
    department: '人资部'
  },
  {
    id: 'FX-007',
    code: 'FX-007',
    level: '中风险',
    levelColor: 'orange',
    category: '信息合规',
    title: '重要业务数据未按规定备份',
    desc: '重要业务数据未按规定备份，存在数据丢失、泄露风险',
    chips: ['信息安全', '数据管理', '信息部'],
    department: '信息部'
  },
  {
    id: 'FX-008',
    code: 'FX-008',
    level: '低风险',
    levelColor: 'default',
    category: '廉洁合规',
    title: '账实不符风险',
    desc: '物资库存管理混乱，账实不符，存在物资损失和舞弊风险',
    chips: ['物资管理', '库存管理', '物资部'],
    department: '物资部'
  }
])

const filteredList = computed(() => {
  const kw = (filters.value.keyword || '').trim()
  return list.value.filter((r) => {
    const hitKw =
      !kw ||
      r.title.includes(kw) ||
      r.desc.includes(kw) ||
      r.category.includes(kw) ||
      r.chips.some((c) => c.includes(kw))
    const hitLevel = !filters.value.level || r.level === filters.value.level
    const hitDept = !filters.value.department || r.department === filters.value.department
    return hitKw && hitLevel && hitDept
  })
})

const handleSearch = () => {
  // 假数据，仅触发过滤
}

const openDetail = (row) => {
  router.push(`/compliance-risk/risk-library/${row.id}`)
}
</script>

<style scoped lang="less">
.rl-page {
  width: 100%;
}

.rl-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.rl-head {
  margin-bottom: 12px;
}

.rl-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-1000);
}

.rl-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.rl-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
}

.rl-search {
  flex: 1 1 360px;
  min-width: 260px;
  :deep(.ant-input-affix-wrapper) {
    border-radius: 10px;
  }
}

.rl-select {
  width: 130px;
}

.rl-summary {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--gray-100);
  font-size: 12px;
  color: var(--gray-600);
}

.rl-list {
  margin-top: 10px;
}

.rl-item {
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

.rl-item-top {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.rl-item-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--gray-1000);
}

.rl-item-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-700);
  line-height: 1.5;
}

.rl-item-chips {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.rl-chip {
  background: rgba(59, 130, 246, 0.08);
  color: var(--gray-700);
  border: none;
}

.rl-item-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  flex: 0 0 auto;
  padding-right: 4px;
}

.rl-code {
  border-radius: 10px;
}

.rl-arrow {
  color: var(--gray-400);
}
</style>

