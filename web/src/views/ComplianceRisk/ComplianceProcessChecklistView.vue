<template>
  <div class="pc-page">
    <div class="pc-card">
      <div class="pc-head">
        <div class="pc-title">流程管控清单</div>
        <div class="pc-subtitle">通过识别业务流程中的合规风险，设置关键风险点，实现“合规入流程”</div>
      </div>

      <div class="pc-filters">
        <a-input
          v-model:value="filters.keyword"
          placeholder="搜索流程名称、合规要点…"
          class="pc-search"
          allow-clear
          @pressEnter="handleSearch"
        >
          <template #prefix>
            <Search size="16" style="color: var(--gray-400)" />
          </template>
        </a-input>
        <a-button type="primary" @click="handleSearch">搜索</a-button>
        <a-select v-model:value="filters.department" class="pc-select" placeholder="全部部门" allow-clear>
          <a-select-option value="物资部">物资部</a-select-option>
          <a-select-option value="建设部">建设部</a-select-option>
          <a-select-option value="财务部">财务部</a-select-option>
          <a-select-option value="法务部">法务部</a-select-option>
          <a-select-option value="营销部">营销部</a-select-option>
        </a-select>
      </div>

      <div class="pc-summary">共 {{ filteredList.length }} 条记录</div>

      <div class="pc-list">
        <div v-for="row in filteredList" :key="row.id" class="pc-item" @click="openDetail(row)">
          <div class="pc-item-main">
            <div class="pc-item-code">{{ row.code }}</div>
            <div class="pc-item-title">{{ row.title }}</div>
            <div class="pc-item-desc">{{ row.desc }}</div>
            <div class="pc-item-meta">
              <a-tag class="pc-chip">{{ row.department }}</a-tag>
              <span class="pc-split"></span>
              <span class="pc-owner">负责人：{{ row.owner }}</span>
            </div>
          </div>
          <ChevronRight class="pc-arrow" size="18" />
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
  {
    id: 'LC-001',
    code: 'LC-001',
    title: '招标采购审批流程',
    desc: '存在规避招标、指定采购等违规风险，影响采购公正性',
    department: '物资部',
    owner: '采购主管',
    compliancePoints: ['采购金额超限触发招标；', '招标文件综合合规审查；', '评标委员会资质/规避组建']
  },
  {
    id: 'LC-002',
    code: 'LC-002',
    title: '工程项目合规审查流程',
    desc: '工程建设存在违规分包、转包，涵盖杜绝廉洁合规风险',
    department: '建设部',
    owner: '工程经理',
    compliancePoints: ['合同文本审查；', '分包资质审核；', '关键节点留痕与复核']
  },
  {
    id: 'LC-003',
    code: 'LC-003',
    title: '财务报销审批流程',
    desc: '报销真实性不合规，超标准报销等财务违规风险',
    department: '财务部',
    owner: '财务主管',
    compliancePoints: ['票据合规性校验；', '预算控制；', '异常报销抽查']
  },
  {
    id: 'LC-005',
    code: 'LC-005',
    title: '合同签订审查流程',
    desc: '合同条款不合规、权利义务失衡等法律合规风险',
    department: '法务部',
    owner: '法务主管',
    compliancePoints: ['合同主体与授权核验；', '条款风险点审查；', '用印/归档闭环']
  },
  {
    id: 'LC-006',
    code: 'LC-006',
    title: '电费核算执行流程',
    desc: '电费计算错误、违规减免电费等营销合规风险',
    department: '营销部',
    owner: '营销主管',
    compliancePoints: ['计量数据核对；', '异常波动复核；', '减免审批留痕']
  }
])

const filteredList = computed(() => {
  const kw = (filters.value.keyword || '').trim()
  return list.value.filter((r) => {
    const hitKw =
      !kw ||
      r.title.includes(kw) ||
      r.desc.includes(kw) ||
      r.compliancePoints.some((p) => p.includes(kw)) ||
      r.department.includes(kw) ||
      r.owner.includes(kw) ||
      r.code.includes(kw)
    const hitDept = !filters.value.department || r.department === filters.value.department
    return hitKw && hitDept
  })
})

const handleSearch = () => {
  // 假数据，仅触发过滤
}

const openDetail = (row) => {
  router.push(`/compliance-risk/process-checklist/${row.id}`)
}
</script>

<style scoped lang="less">
.pc-page {
  width: 100%;
}

.pc-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.pc-head {
  margin-bottom: 12px;
}

.pc-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-1000);
}

.pc-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.pc-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
}

.pc-search {
  flex: 1 1 380px;
  min-width: 260px;
  :deep(.ant-input-affix-wrapper) {
    border-radius: 10px;
  }
}

.pc-select {
  width: 130px;
}

.pc-summary {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--gray-100);
  font-size: 12px;
  color: var(--gray-600);
}

.pc-list {
  margin-top: 10px;
}

.pc-item {
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

.pc-item-code {
  font-size: 12px;
  font-weight: 700;
  color: var(--gray-600);
}

.pc-item-title {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--gray-1000);
}

.pc-item-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-700);
  line-height: 1.5;
}

.pc-item-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--gray-600);
  flex-wrap: wrap;
}

.pc-chip {
  background: rgba(168, 85, 247, 0.1);
  color: #7c3aed;
  border: none;
}

.pc-split {
  width: 1px;
  height: 12px;
  background: var(--gray-200);
}

.pc-arrow {
  color: var(--gray-400);
  flex: 0 0 auto;
  margin-top: 4px;
}
</style>

