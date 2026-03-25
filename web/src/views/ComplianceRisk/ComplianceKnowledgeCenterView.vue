<template>
  <div class="kc-page">
    <div class="hero-card">
      <div class="hero-title">合规知识中心</div>
      <div class="hero-subtitle">一库两清单 · 统一浏览 · 快速查询</div>

      <div class="hero-search">
        <a-input
          v-model:value="keyword"
          placeholder="搜索风险、流程、岗位…"
          size="large"
          class="hero-search-input"
          allow-clear
          @pressEnter="handleSearch"
        />
        <a-button type="primary" size="large" class="hero-search-btn" @click="handleSearch">搜索</a-button>
      </div>
    </div>

    <div class="section">
      <div class="section-title">快捷入口</div>
      <div class="quick-grid">
        <div v-for="item in quickEntries" :key="item.key" class="quick-card" @click="handleQuickOpen(item)">
          <div class="quick-card-top">
            <div class="quick-icon" :class="`t-${item.tone}`">{{ item.iconText }}</div>
            <div class="quick-meta">
              <div class="quick-name">{{ item.name }}</div>
              <div class="quick-desc">{{ item.desc }}</div>
            </div>
          </div>
          <div class="quick-count">
            <span class="quick-count-number">{{ item.count }}</span>
            <span class="quick-count-unit">条记录</span>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">最近更新</div>
      <div class="recent-list">
        <div v-for="row in recentUpdates" :key="row.id" class="recent-row">
          <div class="recent-left">
            <a-tag :color="row.typeColor" class="recent-type">{{ row.type }}</a-tag>
            <div class="recent-content">
              <div class="recent-title">{{ row.title }}</div>
              <div class="recent-sub">
                <span class="recent-role">{{ row.role }}</span>
                <span class="dot">·</span>
                <span class="recent-dept">{{ row.department }}</span>
              </div>
            </div>
          </div>
          <div class="recent-time">{{ row.timeText }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'

const keyword = ref('')

const quickEntries = ref([
  {
    key: 'risk-library',
    name: '合规风险库',
    desc: '风险识别与管控清单',
    count: 8,
    tone: 'red',
    iconText: '风'
  },
  {
    key: 'process-checklist',
    name: '流程管控清单',
    desc: '业务流程与准入管控',
    count: 6,
    tone: 'purple',
    iconText: '流'
  },
  {
    key: 'position-checklist',
    name: '岗位职责清单',
    desc: '岗位合规职责体系',
    count: 8,
    tone: 'green',
    iconText: '岗'
  }
])

const recentUpdates = ref([
  {
    id: 'u1',
    type: '岗位清单',
    typeColor: 'green',
    title: '合规管理专员',
    role: '合规管理部',
    department: '合规管理部',
    timeText: '大约 1 小时前'
  },
  {
    id: 'u2',
    type: '岗位清单',
    typeColor: 'green',
    title: '采购主管',
    role: '物资部',
    department: '物资部',
    timeText: '大约 1 小时前'
  },
  {
    id: 'u3',
    type: '岗位清单',
    typeColor: 'green',
    title: '财务审核员',
    role: '财务部',
    department: '财务部',
    timeText: '大约 1 小时前'
  },
  {
    id: 'u4',
    type: '流程清单',
    typeColor: 'purple',
    title: '招标采购审批流程',
    role: '物资部',
    department: '物资部',
    timeText: '大约 1 小时前'
  },
  {
    id: 'u5',
    type: '流程清单',
    typeColor: 'purple',
    title: '合同签订审查流程',
    role: '法务部',
    department: '法务部',
    timeText: '大约 1 小时前'
  }
])

const handleSearch = () => {
  message.info(`搜索：${keyword.value || '（空）'}（假数据）`)
}

const handleQuickOpen = (item) => {
  message.info(`进入：${item.name}（假数据）`)
}
</script>

<style lang="less" scoped>
.kc-page {
  width: 100%;
}

.hero-card {
  border-radius: 14px;
  padding: 18px 18px 16px 18px;
  color: #fff;
  background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%);
  box-shadow: none;
}

.hero-title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.hero-subtitle {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.9;
}

.hero-search {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.hero-search-input {
  flex: 1;
  min-width: 200px;
  :deep(.ant-input-affix-wrapper) {
    border-radius: 10px;
  }
}

.hero-search-btn {
  border-radius: 10px;
  padding: 0 22px;
}

.section {
  margin-top: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: 10px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.quick-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;

  &:hover {
    background: var(--gray-25);
    border-color: var(--gray-200);
  }
}

.quick-card-top {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.quick-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex: 0 0 auto;

  &.t-red {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
  &.t-purple {
    background: rgba(168, 85, 247, 0.1);
    color: #a855f7;
  }
  &.t-green {
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
  }
}

.quick-meta {
  flex: 1;
  min-width: 0;
}

.quick-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-1000);
  line-height: 1.2;
}

.quick-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--gray-600);
  line-height: 1.2;
}

.quick-count {
  margin-top: 10px;
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.quick-count-number {
  font-size: 22px;
  font-weight: 700;
  color: var(--gray-1000);
}

.quick-count-unit {
  font-size: 12px;
  color: var(--gray-600);
}

.recent-list {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  overflow: hidden;
}

.recent-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--gray-100);

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--gray-25);
  }
}

.recent-left {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.recent-content {
  min-width: 0;
}

.recent-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-1000);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 520px;
}

.recent-sub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--gray-600);
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  color: var(--gray-400);
}

.recent-time {
  flex: 0 0 auto;
  font-size: 12px;
  color: var(--gray-500);
  margin-left: 10px;
}

@media (max-width: 1024px) {
  .quick-grid {
    grid-template-columns: 1fr;
  }
  .recent-title {
    max-width: 320px;
  }
}
</style>

