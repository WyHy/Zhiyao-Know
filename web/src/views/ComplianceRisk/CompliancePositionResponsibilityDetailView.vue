<template>
  <div class="gd-page">
    <div class="gd-top">
      <a-button type="link" class="gd-back" @click="goBack">返回</a-button>
    </div>

    <a-spin :spinning="loading">
      <div class="gd-card">
        <div class="gd-head">
          <div class="gd-title-row">
            <div class="gd-title">{{ record.title }}</div>
            <a-tag class="gd-dept">{{ record.department || '-' }}</a-tag>
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
                <div class="v">{{ record.department || '-' }}</div>
              </div>
              <div class="gd-kv">
                <div class="k">合规类型</div>
                <div class="v">
                  <a-tag class="gd-type">{{ record.compliance_type || '-' }}</a-tag>
                </div>
              </div>
              <div class="gd-kv">
                <div class="k">岗位层级</div>
                <div class="v">{{ record.level || '-' }}</div>
              </div>
            </div>
          </div>

          <div class="gd-section">
            <div class="gd-section-title">岗位职责</div>
            <div class="gd-text">
              <ol class="gd-ol">
                <li v-for="(p, idx) in record.responsibilities || []" :key="idx">{{ p }}</li>
              </ol>
            </div>
          </div>

          <div class="gd-section">
            <div class="gd-section-title">合规要点</div>
            <div class="gd-text">
              <ol class="gd-ol">
                <li v-for="(p, idx) in record.compliance_points || []" :key="idx">{{ p }}</li>
              </ol>
            </div>
          </div>

          <div class="gd-section">
            <div class="gd-section-title">底线标准与处罚</div>
            <div class="gd-text">{{ record.bottom_line_penalty || '-' }}</div>
          </div>

          <div class="gd-section">
            <div class="gd-section-title">合规义务来源</div>
            <div class="gd-text">{{ record.source_basis || '-' }}</div>
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
  const id = Number(route.params.position_id)
  if (!id) return
  loading.value = true
  try {
    const res = await complianceApi.getPositionResponsibilityDetail(id)
    record.value = res.data || {}
  } catch (error) {
    message.error(error.message || '获取岗位详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/compliance-risk/position-responsibility')
}

onMounted(fetchDetail)
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
  white-space: pre-wrap;
}

.gd-ol {
  margin: 0;
  padding-left: 18px;
}
</style>
