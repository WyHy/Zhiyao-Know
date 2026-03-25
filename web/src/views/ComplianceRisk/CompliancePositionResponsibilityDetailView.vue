<template>
  <div class="gd-page">
    <div class="gd-top">
      <a-button type="link" class="gd-back" @click="goBack">返回</a-button>
    </div>

    <div class="gd-card">
      <div class="gd-head">
        <div class="gd-title-row">
          <div class="gd-title">{{ record.title }}</div>
          <a-tag class="gd-dept">{{ record.department }}</a-tag>
        </div>
        <div class="gd-code">岗位编号：{{ record.code }}</div>
      </div>

      <div class="gd-sections">
        <div class="gd-section">
          <div class="gd-section-title">岗位信息</div>
          <div class="gd-grid">
            <div class="gd-kv">
              <div class="k">岗位名称</div>
              <div class="v">{{ record.title }}</div>
            </div>
            <div class="gd-kv">
              <div class="k">所属部门</div>
              <div class="v">{{ record.department }}</div>
            </div>
            <div class="gd-kv">
              <div class="k">合规类型</div>
              <div class="v">
                <a-tag class="gd-type">{{ record.complianceType }}</a-tag>
              </div>
            </div>
            <div class="gd-kv">
              <div class="k">岗位层级</div>
              <div class="v">{{ record.level }}</div>
            </div>
          </div>
        </div>

        <div class="gd-section">
          <div class="gd-section-title">岗位职责</div>
          <div class="gd-text">
            <ol class="gd-ol">
              <li v-for="(p, idx) in record.responsibilities" :key="idx">{{ p }}</li>
            </ol>
          </div>
        </div>

        <div class="gd-section">
          <div class="gd-section-title">合规要点</div>
          <div class="gd-text">
            <ol class="gd-ol">
              <li v-for="(p, idx) in record.compliancePoints" :key="idx">{{ p }}</li>
            </ol>
          </div>
        </div>

        <div class="gd-section">
          <div class="gd-section-title">关联风险库</div>
          <div class="gd-text">
            <a-tag v-for="r in record.relatedRisks" :key="r" class="gd-risk">{{ r }}</a-tag>
          </div>
        </div>

        <div class="gd-section">
          <div class="gd-section-title">管理信息</div>
          <div class="gd-grid">
            <div class="gd-kv">
              <div class="k">岗位编号</div>
              <div class="v">{{ record.code }}</div>
            </div>
            <div class="gd-kv">
              <div class="k">状态</div>
              <div class="v">
                <a-tag color="green">有效</a-tag>
              </div>
            </div>
            <div class="gd-kv">
              <div class="k">录入时间</div>
              <div class="v">{{ record.createdAt }}</div>
            </div>
            <div class="gd-kv">
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
  'GW-001': {
    code: 'GW-001',
    title: '合规管理专员',
    department: '合规管理部',
    complianceType: '法律合规',
    level: '专员',
    responsibilities: ['组织开展合规制度宣贯与培训；', '协助开展合规风险识别与评估；', '对重点事项进行合规审查与留痕'],
    compliancePoints: ['重大事项合规审查需形成书面意见；', '关键流程节点需留痕可追溯；', '发现风险隐患及时上报并推动整改'],
    relatedRisks: ['FX-001', 'FX-005'],
    createdAt: '2026年03月17日 11:46',
    updatedAt: '2026年03月17日 11:46'
  }
}

const record = computed(() => {
  const id = String(route.params.position_id || '')
  return (
    MOCK_MAP[id] || {
      code: id || 'GW-000',
      title: '未找到该岗位（假数据）',
      department: '-',
      complianceType: '-',
      level: '-',
      responsibilities: ['当前岗位编号不存在于死数据中，你可以继续补充 MOCK_MAP。'],
      compliancePoints: ['-'],
      relatedRisks: [],
      createdAt: '-',
      updatedAt: '-'
    }
  )
})

const goBack = () => {
  router.push('/compliance-risk/position-responsibility')
}
</script>

<style scoped lang="less">
.gd-page {
  width: 100%;
}

.gd-top {
  margin-bottom: 10px;
}

.gd-back {
  padding: 0;
  height: auto;
}

.gd-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.gd-head {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--gray-100);
}

.gd-title-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.gd-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--gray-1000);
}

.gd-dept {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
  border: none;
  border-radius: 10px;
}

.gd-code {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.gd-sections {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gd-section {
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 14px;
}

.gd-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--gray-1000);
  margin-bottom: 10px;
}

.gd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 18px;
}

.gd-kv {
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

.gd-type {
  background: rgba(59, 130, 246, 0.08);
  color: var(--gray-700);
  border: none;
  border-radius: 10px;
}

.gd-text {
  font-size: 13px;
  color: var(--gray-900);
  line-height: 1.65;
}

.gd-ol {
  margin: 0;
  padding-left: 18px;
}

.gd-risk {
  margin-right: 8px;
  background: rgba(59, 130, 246, 0.08);
  border: none;
  border-radius: 10px;
  color: var(--gray-700);
}

@media (max-width: 1024px) {
  .gd-grid {
    grid-template-columns: 1fr;
  }
}
</style>

