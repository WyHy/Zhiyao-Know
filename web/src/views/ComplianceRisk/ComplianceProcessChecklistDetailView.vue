<template>
  <div class="pd-page">
    <div class="pd-top">
      <a-button type="link" class="pd-back" @click="goBack">返回</a-button>
    </div>

    <div class="pd-card">
      <div class="pd-head">
        <div class="pd-title-row">
          <div class="pd-title">{{ record.title }}</div>
          <a-tag class="pd-dept">{{ record.department }}</a-tag>
        </div>
        <div class="pd-code">流程编号：{{ record.code }}</div>
      </div>

      <div class="pd-sections">
        <div class="pd-section">
          <div class="pd-section-title">流程信息</div>
          <div class="pd-grid">
            <div class="pd-kv">
              <div class="k">流程名称</div>
              <div class="v">{{ record.title }}</div>
            </div>
            <div class="pd-kv">
              <div class="k">负责部门</div>
              <div class="v">{{ record.department }}</div>
            </div>
            <div class="pd-kv">
              <div class="k">责任部门</div>
              <div class="v">{{ record.department }}</div>
            </div>
            <div class="pd-kv">
              <div class="k">责任人</div>
              <div class="v">{{ record.owner }}</div>
            </div>
          </div>
        </div>

        <div class="pd-section">
          <div class="pd-section-title">风险描述</div>
          <div class="pd-text">{{ record.riskDesc }}</div>
        </div>

        <div class="pd-section">
          <div class="pd-section-title">合规要点</div>
          <div class="pd-text">
            <ol class="pd-ol">
              <li v-for="(p, idx) in record.compliancePoints" :key="idx">{{ p }}</li>
            </ol>
          </div>
        </div>

        <div class="pd-section">
          <div class="pd-section-title">风险管控措施</div>
          <div class="pd-text">{{ record.measures }}</div>
        </div>

        <div class="pd-section">
          <div class="pd-section-title">责任部门</div>
          <div class="pd-grid">
            <div class="pd-kv">
              <div class="k">责任部门</div>
              <div class="v">{{ record.department }}</div>
            </div>
            <div class="pd-kv">
              <div class="k">责任人</div>
              <div class="v">{{ record.owner }}</div>
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
  'LC-001': {
    code: 'LC-001',
    title: '招标采购审批流程',
    department: '物资部',
    owner: '采购主管',
    riskDesc: '存在规避招标、指定采购等违规风险，影响采购公正性',
    compliancePoints: ['采购金额超限触发招标；', '招标文件综合合规审查；', '评标委员会资质/规避组建'],
    measures: '审查采购项目立项资料→确认招标方式→组织公开招标→评标委员会评审→中标公示→合同签订'
  }
}

const record = computed(() => {
  const id = String(route.params.process_id || '')
  return (
    MOCK_MAP[id] || {
      code: id || 'LC-000',
      title: '未找到该流程（假数据）',
      department: '-',
      owner: '-',
      riskDesc: '当前流程编号不存在于死数据中，你可以继续补充 MOCK_MAP。',
      compliancePoints: ['-'],
      measures: '-'
    }
  )
})

const goBack = () => {
  router.push('/compliance-risk/process-checklist')
}
</script>

<style scoped lang="less">
.pd-page {
  width: 100%;
}

.pd-top {
  margin-bottom: 10px;
}

.pd-back {
  padding: 0;
  height: auto;
}

.pd-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.pd-head {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--gray-100);
}

.pd-title-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.pd-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--gray-1000);
}

.pd-dept {
  background: rgba(168, 85, 247, 0.1);
  color: #7c3aed;
  border: none;
  border-radius: 10px;
}

.pd-code {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.pd-sections {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pd-section {
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 14px;
}

.pd-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--gray-1000);
  margin-bottom: 10px;
}

.pd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 18px;
}

.pd-kv {
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

.pd-text {
  font-size: 13px;
  color: var(--gray-900);
  line-height: 1.65;
}

.pd-ol {
  margin: 0;
  padding-left: 18px;
}

@media (max-width: 1024px) {
  .pd-grid {
    grid-template-columns: 1fr;
  }
}
</style>

