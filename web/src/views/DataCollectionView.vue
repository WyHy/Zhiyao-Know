<template>
  <div class="data-collection-view">
    <!-- 左侧子菜单导航 -->
    <div class="submenu-sidebar">
      <RouterLink
        to="/data-collection/monitoring-config"
        class="submenu-item"
        :class="{ active: route.path.includes('monitoring-config') }"
      >
        监控配置
      </RouterLink>
      <RouterLink
        to="/data-collection/data-extraction"
        class="submenu-item"
        :class="{ active: route.path.includes('data-extraction') }"
      >
        数据提取
      </RouterLink>
      <RouterLink
        to="/data-collection/log-management"
        class="submenu-item"
        :class="{ active: route.path.includes('log-management') }"
      >
        日志管理
      </RouterLink>
    </div>
    <!-- 右侧内容区域 -->
    <div class="content-area">
      <MonitoringConfigView v-if="route.path.includes('monitoring-config')" />
      <DataExtractionView v-else-if="route.path.includes('data-extraction')" />
      <LogManagementView v-else-if="route.path.includes('log-management')" />
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import MonitoringConfigView from './DataCollection/MonitoringConfigView.vue'
import DataExtractionView from './DataCollection/DataExtractionView.vue'
import LogManagementView from './DataCollection/LogManagementView.vue'

const route = useRoute()
</script>

<style lang="less" scoped>
.data-collection-view {
  height: 100%;
  display: flex;
  background: #ffffff;
}

.submenu-sidebar {
  width: 200px;
  background: #fafafa;
  border-right: 1px solid #f0f0f0;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;

  .submenu-item {
    padding: 12px 24px;
    color: #666;
    text-decoration: none;
    font-size: 14px;
    transition: all 0.2s;
    cursor: pointer;
    border-left: 3px solid transparent;

    &:hover {
      background: #f5f5f5;
      color: #1890ff;
    }

    &.active {
      background: #e6f7ff;
      color: #1890ff;
      border-left-color: #1890ff;
      font-weight: 500;
    }
  }
}

.content-area {
  flex: 1;
  overflow: auto;
}
</style>