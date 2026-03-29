<template>
  <div class="rd-page">
    <div class="rd-top">
      <a-button type="link" class="rd-back" @click="goBack">返回</a-button>
    </div>

    <a-spin :spinning="loading">
      <div class="rd-card">
        <div class="rd-head">
          <div class="rd-title-row">
            <div class="rd-title">{{ record.title }}</div>
            <a-tag :color="levelColor">{{ record.level || '未分级' }}</a-tag>
          </div>
          <div class="rd-code">风险编号：{{ record.code }}</div>
        </div>

        <div class="rd-sections">
          <div class="rd-section">
            <div class="rd-section-title">业务信息</div>
            <div class="rd-grid">
              <div class="rd-kv">
                <div class="k">一级业务</div>
                <div class="v">{{ record.business_lv1 || '-' }}</div>
              </div>
              <div class="rd-kv">
                <div class="k">二级业务</div>
                <div class="v">{{ record.business_lv2 || '-' }}</div>
              </div>
              <div class="rd-kv">
                <div class="k">合规类型</div>
                <div class="v">{{ record.category || '-' }}</div>
              </div>
              <div class="rd-kv">
                <div class="k">底线</div>
                <div class="v">{{ record.bottom_line || '-' }}</div>
              </div>
            </div>
          </div>

          <div class="rd-section">
            <div class="rd-section-title">风险信息</div>
            <div class="rd-grid">
              <div class="rd-kv">
                <div class="k">风险等级</div>
                <div class="v">
                  <a-tag :color="levelColor">{{ record.level || '未分级' }}</a-tag>
                </div>
              </div>
              <div class="rd-kv span-2">
                <div class="k">风险描述</div>
                <div class="v">{{ record.desc || '-' }}</div>
              </div>
              <div class="rd-kv span-2">
                <div class="k">责任或后果</div>
                <div class="v">{{ record.consequence || '-' }}</div>
              </div>
            </div>
          </div>

          <div class="rd-section">
            <div class="rd-section-title">合规依据</div>
            <div class="rd-text">{{ record.basis || '-' }}</div>
          </div>

          <div class="rd-section">
            <div class="rd-section-title">合规义务</div>
            <div class="rd-text">{{ record.obligation || '-' }}</div>
          </div>

          <div class="rd-section">
            <div class="rd-section-title">管控措施</div>
            <div class="rd-text">
              <ol class="rd-ol">
                <li v-for="(m, idx) in record.measures || []" :key="idx">{{ m }}</li>
              </ol>
            </div>
          </div>

          <div class="rd-section">
            <div class="rd-section-title">责任部门</div>
            <div class="rd-grid">
              <div class="rd-kv">
                <div class="k">归口部门</div>
                <div class="v">{{ record.department || '-' }}</div>
              </div>
              <div class="rd-kv">
                <div class="k">配合部门</div>
                <div class="v">{{ record.cooperate_department || '-' }}</div>
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
                <div class="k">录入时间</div>
                <div class="v">{{ record.created_at || '-' }}</div>
              </div>
              <div class="rd-kv">
                <div class="k">最后更新</div>
                <div class="v">{{ record.updated_at || '-' }}</div>
              </div>
              <div class="rd-kv">
                <div class="k">备注</div>
                <div class="v">{{ record.remark || '-' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <a-empty v-if="!loading && !record.id" description="记录不存在" />
    </a-spin>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { complianceApi } from '@/apis/compliance_api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const record = ref({})

const levelColor = computed(() => {
  if (record.value.level === '高风险') return 'red'
  if (record.value.level === '中风险') return 'orange'
  if (record.value.level === '低风险') return 'green'
  return 'default'
})

const fetchDetail = async () => {
  const id = Number(route.params.risk_id)
  if (!id) return
  loading.value = true
  try {
    const res = await complianceApi.getRiskLibraryDetail(id)
    record.value = res.data || {}
  } catch (error) {
    message.error(error.message || '获取风险详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/compliance-risk/risk-library')
}

onMounted(fetchDetail)
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
  white-space: pre-wrap;
}

.rd-ol {
  margin: 0;
  padding-left: 18px;
}
</style>
