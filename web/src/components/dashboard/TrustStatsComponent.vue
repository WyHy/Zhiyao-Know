<template>
  <a-card title="可信检索监控" :loading="loading" class="dashboard-card">
    <div class="trust-stats">
      <div class="metric-block">
        <div class="metric-title">Grounded 质量（7天）</div>
        <div class="metric-grid">
          <div class="metric-item">
            <span class="label">低可信占比</span>
            <span class="value">{{ toPercent(groundedStats?.low_grounded_rate) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">平均支持度</span>
            <span class="value">{{ toPercent(groundedStats?.avg_support_ratio) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">重试事件</span>
            <span class="value">{{ groundedStats?.grounded_retry_events ?? 0 }}</span>
          </div>
        </div>
      </div>

      <div class="metric-block">
        <div class="metric-title">跨库路由（7天）</div>
        <div class="metric-grid">
          <div class="metric-item">
            <span class="label">路由次数</span>
            <span class="value">{{ routeStats?.total_route_events ?? 0 }}</span>
          </div>
          <div class="metric-item">
            <span class="label">不足证据次数</span>
            <span class="value">{{ routeStats?.insufficient_events ?? 0 }}</span>
          </div>
          <div class="metric-item">
            <span class="label">平均候选库数</span>
            <span class="value">{{ toFixed(routeStats?.avg_candidate_count) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">预算截断率</span>
            <span class="value">{{ toPercent(routeStats?.budget_truncated_rate) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">平均预算占用</span>
            <span class="value">{{ toPercent(routeStats?.avg_budget_utilization) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">平均估算Token</span>
            <span class="value">{{ toFixed(routeStats?.avg_estimated_tokens) }}</span>
          </div>
        </div>
        <div class="top-kb-line">
          <span class="label">Top 命中库</span>
          <span class="value">{{ topKbText }}</span>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  groundedStats: {
    type: Object,
    default: null
  },
  routeStats: {
    type: Object,
    default: null
  }
})

const toPercent = (value) => {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0.00%'
  return `${(n * 100).toFixed(2)}%`
}

const toFixed = (value) => {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0.00'
  return n.toFixed(2)
}

const topKbText = computed(() => {
  const top = props.routeStats?.top_hit_kbs || []
  if (!Array.isArray(top) || top.length === 0) return '-'
  return top
    .slice(0, 3)
    .map((item) => `${item.name}(${item.count})`)
    .join(' / ')
})
</script>

<style scoped lang="less">
.trust-stats {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.metric-block {
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  padding: 10px 12px;
  background-color: var(--gray-25);
}

.metric-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: 8px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 3px;

  .label {
    font-size: 12px;
    color: var(--gray-600);
  }

  .value {
    font-size: 16px;
    font-weight: 600;
    color: var(--gray-900);
    line-height: 1.2;
  }
}

.top-kb-line {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  align-items: flex-start;

  .label {
    font-size: 12px;
    color: var(--gray-600);
    white-space: nowrap;
  }

  .value {
    font-size: 12px;
    color: var(--gray-800);
  }
}

@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
