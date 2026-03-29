<template>
  <div class="pd-page">
    <div class="pd-top">
      <a-button type="link" class="pd-back" @click="goBack">返回</a-button>
    </div>

    <a-spin :spinning="loading">
      <div class="pd-card">
        <div class="pd-head">
          <div class="pd-title-row">
            <div class="pd-title">{{ record.title }}</div>
            <a-tag class="pd-dept">{{ record.department || '-' }}</a-tag>
          </div>
          <div class="pd-code">流程编号：{{ record.code }}</div>
        </div>

        <div class="pd-sections">
          <div class="pd-section">
            <div class="pd-section-title">流程信息</div>
            <div class="pd-grid">
              <div class="pd-kv">
                <div class="k">一级流程</div>
                <div class="v">{{ record.level1_process || '-' }}</div>
              </div>
              <div class="pd-kv">
                <div class="k">二级流程</div>
                <div class="v">{{ record.level2_process || '-' }}</div>
              </div>
              <div class="pd-kv">
                <div class="k">三级流程</div>
                <div class="v">{{ record.level3_process || '-' }}</div>
              </div>
              <div class="pd-kv">
                <div class="k">责任部门</div>
                <div class="v">{{ record.department || '-' }}</div>
              </div>
            </div>
          </div>

          <div class="pd-section">
            <div class="pd-section-title">风险描述</div>
            <div class="pd-text">{{ record.risk_desc || '-' }}</div>
          </div>

          <div class="pd-section">
            <div class="pd-section-title">合规要点</div>
            <div class="pd-text">
              <ol class="pd-ol">
                <li v-for="(p, idx) in record.compliance_points || []" :key="idx">{{ p }}</li>
              </ol>
            </div>
          </div>

          <div class="pd-section">
            <div class="pd-section-title">合规风险点</div>
            <div class="pd-text">{{ record.risk_points || '-' }}</div>
          </div>

          <div class="pd-section">
            <div class="pd-section-title">监督评价要点</div>
            <div class="pd-text">{{ record.measures || '-' }}</div>
          </div>

          <div class="pd-section">
            <div class="pd-section-title">合规义务来源</div>
            <div class="pd-text">{{ record.source_basis || '-' }}</div>
          </div>
        </div>
      </div>
      <a-empty v-if="!loading && !record.id" description="记录不存在" />
    </a-spin>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { complianceApi } from '@/apis/compliance_api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const record = ref({})

const fetchDetail = async () => {
  const id = Number(route.params.process_id)
  if (!id) return
  loading.value = true
  try {
    const res = await complianceApi.getProcessChecklistDetail(id)
    record.value = res.data || {}
  } catch (error) {
    message.error(error.message || '获取流程详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/compliance-risk/process-checklist')
}

onMounted(fetchDetail)
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
  white-space: pre-wrap;
}

.pd-ol {
  margin: 0;
  padding-left: 18px;
}
</style>
