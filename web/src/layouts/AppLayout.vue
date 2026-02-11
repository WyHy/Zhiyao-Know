<script setup>
import { ref, reactive, onMounted, computed, provide, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Bot, Waypoints, LibraryBig, BarChart3, CircleCheck, Folder, FileSearch, MessageCircle, FileText, Database, FileCheck } from 'lucide-vue-next'

import { useConfigStore } from '@/stores/config'
import { useDatabaseStore } from '@/stores/database'
import { useInfoStore } from '@/stores/info'
import { useTaskerStore } from '@/stores/tasker'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import DebugComponent from '@/components/DebugComponent.vue'
import TaskCenterDrawer from '@/components/TaskCenterDrawer.vue'
import SettingsModal from '@/components/SettingsModal.vue'

const configStore = useConfigStore()
const databaseStore = useDatabaseStore()
const infoStore = useInfoStore()
const taskerStore = useTaskerStore()
const userStore = useUserStore()
const { activeCount: activeCountRef, isDrawerOpen } = storeToRefs(taskerStore)

const layoutSettings = reactive({
  showDebug: false,
  useTopBar: false // 是否使用顶栏
})

// GitHub stars removed

// Add state for debug modal
const showDebugModal = ref(false)

// Add state for settings modal
const showSettingsModal = ref(false)

// Provide settings modal methods to child components
const openSettingsModal = () => {
  showSettingsModal.value = true
}

// Handle debug modal close
const handleDebugModalClose = () => {
  showDebugModal.value = false
}

const getRemoteConfig = () => {
  configStore.refreshConfig()
}

const getRemoteDatabase = () => {
  // 只有管理员才需要加载知识库列表
  if (userStore.isAdmin) {
    databaseStore.loadDatabases().catch((error) => {
      // 静默处理错误，避免普通用户看到权限错误提示
      console.error('加载知识库列表失败:', error)
    })
  }
}

// GitHub stars fetch removed

onMounted(async () => {
  // 加载信息配置
  await infoStore.loadInfoConfig()
  // 加载其他配置
  getRemoteConfig()
  getRemoteDatabase()
  // 任务中心暂时注释，预加载任务数据也注释
  // taskerStore.loadTasks()
})

// 打印当前页面的路由信息，使用 vue3 的 setup composition API
const route = useRoute()
console.log(route)

const activeTaskCount = computed(() => activeCountRef.value || 0)

// 下面是导航菜单部分
const mainList = computed(() => {
  const isAdmin = userStore.isAdmin
  const list = []
  
  // // 智能体菜单（仅管理员可见）
  // if (isAdmin) {
  //   list.push({
  //     name: '智能体',
  //     path: '/agent',
  //     icon: Bot,
  //     activeIcon: Bot,
  //     hidden: false
  //   })
  // }
  
  // // 知识图谱菜单（仅管理员可见）
  // if (isAdmin) {
  //   list.push({
  //     name: '知识图谱',
  //     path: '/graph',
  //     icon: Waypoints,
  //     activeIcon: Waypoints,
  //     hidden: false
  //   })
  // }
  
  // 对话菜单（所有用户可见）
  list.push({
    name: '对话',
    path: '/chat',
    icon: MessageCircle,
    activeIcon: MessageCircle,
    hidden: false
  })
  
  // 知识库菜单（所有用户可见）
  list.push({
    name: '知识库',
    path: '/knowledge',
    icon: FileSearch,
    activeIcon: FileSearch,
    hidden: false
  })
  
  // 知识库管理菜单（仅管理员可见）
  if (isAdmin) {
    list.push({
      name: '知识库管理',
      path: '/database',
      icon: Folder,
      activeIcon: Folder,
      hidden: false
    })
  }
  
  // 数据采集菜单（仅管理员可见）
  if (isAdmin) {
    list.push({
      name: '数据采集',
      path: '/data-collection/monitoring-config',
      icon: Database,
      activeIcon: Database,
      hidden: false
    })
  }
  
  // // 仪表板菜单（仅管理员可见）
  // if (isAdmin) {
  //   list.push({
  //     name: '仪表板',
  //     path: '/dashboard',
  //     icon: BarChart3,
  //     activeIcon: BarChart3,
  //     hidden: false
  //   })
  // }
  
  return list
})

// Provide settings modal methods to child components
provide('settingsModal', {
  openSettingsModal
})
</script>

<template>
  <div class="app-layout" :class="{ 'use-top-bar': layoutSettings.useTopBar }">
    <div class="header" :class="{ 'top-bar': layoutSettings.useTopBar }">
      <div class="logo circle">
        <img :src="infoStore.organization.avatar" />
      </div>
      <div class="nav">
        <!-- 使用mainList渲染导航项 -->
        <RouterLink
          v-for="(item, index) in mainList"
          :key="index"
          :to="item.path"
          v-show="!item.hidden"
          class="nav-item"
          :class="{ active: route.path === item.path || route.path.startsWith(item.path + '/') }"
        >
          <div class="nav-item-content">
            <component
              class="icon"
              :is="route.path === item.path || route.path.startsWith(item.path + '/') ? item.activeIcon : item.icon"
              size="22"
            />
            <span class="nav-item-text">{{ item.name }}</span>
          </div>
        </RouterLink>
        <!-- 任务中心菜单暂时注释 -->
        <!-- <div
          class="nav-item task-center"
          :class="{ active: isDrawerOpen }"
          @click="taskerStore.openDrawer()"
        >
          <a-tooltip placement="right">
            <template #title>任务中心</template>
            <a-badge
              :count="activeTaskCount"
              :overflow-count="99"
              class="task-center-badge"
              size="small"
            >
              <CircleCheck class="icon" size="22" />
            </a-badge>
          </a-tooltip>
        </div> -->
      </div>
      <div class="fill"></div>
      <!-- 用户信息组件 -->
      <div class="nav-item user-info">
        <UserInfoComponent />
      </div>
    </div>
    <router-view v-slot="{ Component, route }" id="app-router-view">
      <keep-alive v-if="route.meta.keepAlive !== false">
        <component :is="Component" />
      </keep-alive>
      <component :is="Component" v-else />
    </router-view>

    <!-- Debug Modal -->
    <a-modal
      v-model:open="showDebugModal"
      title="调试面板"
      width="90%"
      :footer="null"
      @cancel="handleDebugModalClose"
      :maskClosable="true"
      :destroyOnClose="true"
      class="debug-modal"
    >
      <DebugComponent />
    </a-modal>
    <!-- 任务中心抽屉暂时注释 -->
    <!-- <TaskCenterDrawer /> -->
    <SettingsModal v-model:visible="showSettingsModal" @close="() => (showSettingsModal = false)" />
  </div>
</template>

<style lang="less" scoped>
// Less 变量定义
@header-width: 200px;

.app-layout {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  min-width: var(--min-width);
}

div.header,
#app-router-view {
  // height: 100%;
  max-width: 100%;
  user-select: none;
}

#app-router-view {
  flex: 1 1 auto;
  overflow-y: auto;
}

  .header {
    display: flex;
    flex-direction: column;
    flex: 0 0 @header-width;
    justify-content: flex-start;
    align-items: center;
    background-color: #F2F3F5; /* 浅灰色背景 */
    height: 100%;
    width: @header-width;
    border-right: 1px solid var(--gray-200);
    padding: 0 4px;

  .nav {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    position: relative;
    // height: 45px;
    gap: 16px;
    width: 100%;
    padding: 0 8px;
  }

  .fill {
    flex-grow: 1;
  }

  .logo {
    width: 34px;
    height: 34px;
    margin: 6px 0 20px 0;

    img {
      width: 100%;
      height: 100%;
      border-radius: 4px; // 50% for circle
    }

    & > a {
      text-decoration: none;
      font-size: 24px;
      font-weight: bold;
      color: var(--gray-900);
    }
  }

  .nav-item-wrapper {
    width: 100%;
  }

  .nav-item {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    width: 100%;
    min-height: 44px;
    padding: 8px 0;
    border: 1px solid transparent;
    border-radius: 8px;
    background-color: transparent;
    color: #333333; /* 淡灰色背景下的图标颜色 */
    font-size: 20px;
    transition:
      background-color 0.2s ease-in-out,
      color 0.2s ease-in-out;
    margin: 0 4px;
    text-decoration: none;
    cursor: pointer;
    outline: none;

    &.has-children {
      cursor: pointer;
    }

    .nav-item-link {
      width: 100%;
      text-decoration: none;
      color: inherit;
    }

    .nav-item-content {
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: flex-start;
      gap: 8px;
      width: 100%;
      padding: 0 8px;

      .submenu-arrow {
        margin-left: auto;
        font-size: 10px;
        transition: transform 0.2s;
        color: #8c8c8c;

        &.expanded {
          transform: rotate(180deg);
        }
      }
    }

    .nav-item-text {
      font-size: 13px;
      color: #333333; /* 淡灰色背景下的深色文字 */
      line-height: 1.2;
      text-align: left;
      white-space: nowrap;
      transition: color 0.2s ease-in-out;
      font-weight: 500;
    }

    & > svg:focus {
      outline: none;
    }
    & > svg:focus-visible {
      outline: none;
    }

    &.active {
      background-color: rgba(0, 0, 0, 0.05); /* 淡灰色背景下的激活状态 */
      font-weight: bold;
      color: var(--main-color);

      .nav-item-text {
        color: var(--main-color);
        font-weight: 500;
      }
    }

    &.warning {
      color: var(--color-error-500);
    }

    &:hover {
      background-color: rgba(0, 0, 0, 0.03); /* 淡灰色背景下的悬停效果 */
      color: var(--main-color);

      .nav-item-text {
        color: var(--main-color);
      }
    }

    &.has-children.active {
      background-color: rgba(0, 0, 0, 0.05);
    }

    &.github {
      padding: 10px 12px;
      margin-bottom: 16px;
      &:hover {
        background-color: transparent;
        border: 1px solid transparent;
      }

      .github-link {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: inherit;
      }

      .github-stars {
        display: flex;
        align-items: center;
        font-size: 12px;
        margin-top: 4px;

        .star-icon {
          color: var(--color-warning-500);
          font-size: 12px;
          margin-right: 2px;
        }

        .star-count {
          font-weight: 600;
        }
      }
    }

    &.api-docs {
      padding: 10px 12px;
    }
    &.docs {
      display: none;
    }
    &.task-center {
      .task-center-badge {
        width: 100%;
        display: flex;
        justify-content: center;
      }
    }

    &.theme-toggle-nav {
      .theme-toggle-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        cursor: pointer;
        color: var(--gray-1000);
        transition: color 0.2s ease-in-out;

        &:hover {
          color: var(--main-color);
        }
      }
    }
    &.user-info {
      margin-bottom: 8px;
      width: 100%;
      justify-content: flex-start;
      padding: 8px;
    }
  }

  .submenu {
    margin-left: 24px;
    margin-top: 4px;
    margin-bottom: 4px;

    .submenu-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-radius: 6px;
      text-decoration: none;
      color: #666;
      font-size: 12px;
      transition: all 0.2s;
      margin: 2px 4px;

      .submenu-item-text {
        font-size: 12px;
      }

      &.active {
        background-color: rgba(24, 144, 255, 0.1);
        color: var(--main-color);
        font-weight: 500;
      }

      &:hover {
        background-color: rgba(0, 0, 0, 0.03);
        color: var(--main-color);
      }
    }
  }
}

.app-layout.use-top-bar {
  flex-direction: column;
}

.header.top-bar {
  flex-direction: row;
  flex: 0 0 50px;
  width: 100%;
  height: 50px;
  border-right: none;
  border-bottom: 1px solid var(--main-40);
  background-color: var(--main-20);
  padding: 0 20px;
  gap: 24px;

  .logo {
    width: fit-content;
    height: 28px;
    margin-right: 16px;
    display: flex;
    align-items: center;

    a {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: inherit;
    }

    img {
      width: 28px;
      height: 28px;
      margin-right: 8px;
    }
  }

  .nav {
    flex-direction: row;
    height: auto;
    gap: 20px;
  }

  .nav-item {
    flex-direction: row;
    width: auto;
    padding: 4px 16px;
    margin: 0;

    .icon {
      margin-right: 8px;
      font-size: 15px; // 减小图标大小
      border: none;
      outline: none;
      color: #333333; /* 淡灰色背景下的图标颜色 */

      &:focus,
      &:active {
        border: none;
        outline: none;
      }
    }

    .text {
      margin-top: 0;
      font-size: 15px;
    }

    &.github {
      padding: 8px 12px;

      .icon {
        margin-right: 0;
        font-size: 18px;
      }

      &.active {
        color: var(--main-color);
      }

      a {
        display: flex;
        align-items: center;
      }

      .github-stars {
        display: flex;
        align-items: center;
        margin-left: 6px;

        .star-icon {
          color: var(--color-warning-500);
          font-size: 14px;
          margin-right: 2px;
        }
      }
    }

    &.theme-toggle-nav {
      padding: 8px 12px;

      .theme-toggle-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--gray-1000);
        transition: color 0.2s ease-in-out;
        cursor: pointer;

        &:hover {
          color: var(--main-color);
        }
      }

      &.active {
        .theme-toggle-icon {
          color: var(--main-color);
        }
      }
    }
  }
}
</style>
