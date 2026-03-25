<template>
  <div class="rd-page">
    <div class="rd-top">
      <a-button type="link" class="rd-back" @click="goBack">返回</a-button>
    </div>

    <div class="rd-card">
      <div class="rd-head">
        <div class="rd-title-row">
          <div class="rd-title">{{ record.title }}</div>
          <a-tag :color="record.levelColor">{{ record.level }}</a-tag>
        </div>
        <div class="rd-code">风险编号：{{ record.code }}</div>
      </div>

      <div class="rd-sections">
        <div class="rd-section">
          <div class="rd-section-title">业务信息</div>
          <div class="rd-grid">
            <div class="rd-kv">
              <div class="k">业务类型</div>
              <div class="v">{{ record.bizType }}</div>
            </div>
            <div class="rd-kv">
              <div class="k">业务活动</div>
              <div class="v">{{ record.bizActivity }}</div>
            </div>
            <div class="rd-kv">
              <div class="k">合规类型</div>
              <div class="v">{{ record.category }}</div>
            </div>
            <div class="rd-kv">
              <div class="k">发生概率</div>
              <div class="v">{{ record.probability }}</div>
            </div>
          </div>
        </div>

        <div class="rd-section">
          <div class="rd-section-title">风险信息</div>
          <div class="rd-grid">
            <div class="rd-kv">
              <div class="k">风险等级</div>
              <div class="v">
                <a-tag :color="record.levelColor">{{ record.level }}</a-tag>
              </div>
            </div>
            <div class="rd-kv span-2">
              <div class="k">风险描述</div>
              <div class="v">{{ record.desc }}</div>
            </div>
          </div>
        </div>

        <div class="rd-section">
          <div class="rd-section-title">合规依据</div>
          <div class="rd-text">{{ record.basis }}</div>
        </div>

        <div class="rd-section">
          <div class="rd-section-title">管控措施</div>
          <div class="rd-text">
            <ol class="rd-ol">
              <li v-for="(m, idx) in record.measures" :key="idx">{{ m }}</li>
            </ol>
          </div>
        </div>

        <div class="rd-section">
          <div class="rd-section-title">责任部门</div>
          <div class="rd-grid">
            <div class="rd-kv">
              <div class="k">责任部门</div>
              <div class="v">{{ record.department }}</div>
            </div>
            <div class="rd-kv">
              <div class="k">责任人</div>
              <div class="v">{{ record.owner }}</div>
            </div>
          </div>
        </div>

        <div class="rd-section">
          <div class="rd-section-title">管理信息</div>
          <div class="rd-grid">
            <div class="rd-kv">
              <div class="k">风险编号</div>
              <div class="v">{{ record.code }}</div>
            </div>
            <div class="rd-kv">
              <div class="k">记录状态</div>
              <div class="v">
                <a-tag color="green">有效</a-tag>
              </div>
            </div>
            <div class="rd-kv">
              <div class="k">录入时间</div>
              <div class="v">{{ record.createdAt }}</div>
            </div>
            <div class="rd-kv">
              <div class="k">最后更新</div>
              <div class="v">{{ record.updatedAt }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const MOCK_MAP = {
  'FX-001': {
    code: 'FX-001',
    level: '高风险',
    levelColor: 'red',
    category: '法律合规',
    title: '采购项目立项',
    desc: '未按规定履行招标程序，存在规避招标、化整为零规避招标等违规行为',
    bizType: '招标采购',
    bizActivity: '采购项目立项',
    probability: '中等',
    basis: '《招标投标法》及相关规定，第三十条、第四十条等（示例文本）',
    measures: ['严格执行招标采购管理制度；', '建立招标采购审查机制；', '定期开展招标采购合规培训'],
    department: '物资部',
    owner: '采购主管',
    createdAt: '2026年03月17日 11:46',
    updatedAt: '2026年03月17日 11:46'
  }
}

const record = computed(() => {
  const id = String(route.params.risk_id || '')
  return (
    MOCK_MAP[id] || {
      code: id || 'FX-000',
      level: '中风险',
      levelColor: 'orange',
      category: '合规',
      title: '未找到该风险（假数据）',
      desc: '当前风险编号不存在于死数据中，你可以继续补充 MOCK_MAP。',
      bizType: '-',
      bizActivity: '-',
      probability: '-',
      basis: '-',
      measures: ['-'],
      department: '-',
      owner: '-',
      createdAt: '-',
      updatedAt: '-'
    }
  )
})

const goBack = () => {
  router.push('/compliance-risk/risk-library')
}
</script>

<style scoped lang="less">
.rd-page {
  width: 100%;
}

.rd-top {
  margin-bottom: 10px;
}

.rd-back {
  padding: 0;
  height: auto;
}

.rd-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.rd-head {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--gray-100);
}

.rd-title-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.rd-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--gray-1000);
}

.rd-code {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.rd-sections {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rd-section {
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 14px;
}

.rd-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--gray-1000);
  margin-bottom: 10px;
}

.rd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 18px;
}

.rd-kv {
  .k {
    font-size: 12px;
    color: var(--gray-500);
    margin-bottom: 6px;
  }
  .v {
    font-size: 13px;
    color: var(--gray-900);
    line-height: 1.55;
  }
}

.span-2 {
  grid-column: 1 / 3;
}

.rd-text {
  font-size: 13px;
  color: var(--gray-900);
  line-height: 1.65;
}

.rd-ol {
  margin: 0;
  padding-left: 18px;
}

@media (max-width: 1024px) {
  .rd-grid {
    grid-template-columns: 1fr;
  }
  .span-2 {
    grid-column: 1 / 2;
  }
}
</style>

