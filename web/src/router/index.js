import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import BlankLayout from '@/layouts/BlankLayout.vue'
import { useUserStore } from '@/stores/user'
import { useAgentStore } from '@/stores/agent'

// 临时：无后台/联调阶段可跳过登录（随时可改回）
// 用法：在 `web/.env.local`（或对应环境文件）里加 `VITE_BYPASS_AUTH=true`
const BYPASS_AUTH = import.meta.env.VITE_BYPASS_AUTH === 'true'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/agent',
      name: 'AgentMain',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'AgentComp',
          component: () => import('../views/AgentView.vue'),
          meta: { keepAlive: true, requiresAuth: true, requiresAdmin: true }
        }
      ]
    },
    {
      path: '/agent/:agent_id',
      name: 'AgentSinglePage',
      component: () => import('../views/AgentSingleView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/graph',
      name: 'graph',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'GraphComp',
          component: () => import('../views/GraphView.vue'),
          meta: { keepAlive: false, requiresAuth: true, requiresAdmin: true }
        }
      ]
    },
    {
      path: '/database',
      name: 'database',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'DatabaseComp',
          component: () => import('../views/DataBaseView.vue'),
          meta: { keepAlive: true, requiresAuth: true, requiresAdmin: true }
        },
        {
          path: ':database_id',
          name: 'DatabaseInfoComp',
          component: () => import('../views/DataBaseInfoView.vue'),
          meta: { keepAlive: false, requiresAuth: true, requiresAdmin: true }
        }
      ]
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'DashboardComp',
          component: () => import('../views/DashboardView.vue'),
          meta: { keepAlive: false, requiresAuth: true, requiresAdmin: true }
        }
      ]
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'KnowledgeComp',
          component: () => import('../views/KnowledgeView.vue'),
          meta: { keepAlive: true, requiresAuth: true }
        }
      ]
    },
    {
      path: '/chat',
      name: 'chat',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'ChatComp',
          component: () => import('../views/ChatView.vue'),
          meta: { keepAlive: true, requiresAuth: true }
        }
      ]
    },
    {
      path: '/chat-with-agent',
      name: 'chat-with-agent',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'ChatWithAgentComp',
          component: () => import('../views/ChatWithAgentView.vue'),
          meta: { keepAlive: false, requiresAuth: true }
        }
      ]
    },
    {
      path: '/data-collection',
      name: 'data-collection',
      component: AppLayout,
      children: [
        {
          path: 'monitoring-config',
          name: 'MonitoringConfig',
          component: () => import('../views/DataCollection/MonitoringConfigView.vue'),
          meta: { keepAlive: true, requiresAuth: true, requiresAdmin: true }
        },
        {
          path: 'data-extraction',
          name: 'DataExtraction',
          component: () => import('../views/DataCollection/DataExtractionView.vue'),
          meta: { keepAlive: true, requiresAuth: true, requiresAdmin: true }
        },
        {
          path: 'log-management',
          name: 'LogManagement',
          component: () => import('../views/DataCollection/LogManagementView.vue'),
          meta: { keepAlive: true, requiresAuth: true, requiresAdmin: true }
        }
      ]
    },
    {
      path: '/compliance-risk',
      name: 'compliance-risk',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'ComplianceRiskLayoutComp',
          component: () => import('../views/ComplianceRisk/ComplianceRiskLayout.vue'),
          meta: { keepAlive: false, requiresAuth: true },
          children: [
            {
              path: '',
              redirect: '/compliance-risk/knowledge'
            },
            {
              path: 'knowledge',
              name: 'ComplianceKnowledgeCenterComp',
              component: () => import('../views/ComplianceRisk/ComplianceKnowledgeCenterView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'risk-library',
              name: 'ComplianceRiskLibraryComp',
              component: () => import('../views/ComplianceRisk/ComplianceRiskLibraryView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'risk-library/:risk_id',
              name: 'ComplianceRiskLibraryDetailComp',
              component: () => import('../views/ComplianceRisk/ComplianceRiskLibraryDetailView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'process-checklist',
              name: 'ComplianceProcessChecklistComp',
              component: () => import('../views/ComplianceRisk/ComplianceProcessChecklistView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'process-checklist/:process_id',
              name: 'ComplianceProcessChecklistDetailComp',
              component: () => import('../views/ComplianceRisk/ComplianceProcessChecklistDetailView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'position-responsibility',
              name: 'CompliancePositionResponsibilityComp',
              component: () => import('../views/ComplianceRisk/CompliancePositionResponsibilityView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'position-responsibility/:position_id',
              name: 'CompliancePositionResponsibilityDetailComp',
              component: () => import('../views/ComplianceRisk/CompliancePositionResponsibilityDetailView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            },
            {
              path: 'data-import',
              name: 'ComplianceDataImportComp',
              component: () => import('../views/ComplianceRisk/ComplianceDataImportView.vue'),
              meta: { keepAlive: false, requiresAuth: true }
            }
          ]
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('../views/EmptyView.vue'),
      meta: { requiresAuth: false }
    }
  ]
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 临时跳过登录：默认让 `/` 进入“首页”（这里用知识库页）
  if (BYPASS_AUTH) {
    if (to.path === '/') {
      next('/knowledge')
      return
    }
    next()
    return
  }

  // 检查路由是否需要认证
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth === true)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin)

  const userStore = useUserStore()

  // 如果有 token 但用户信息未加载，先获取用户信息
  if (userStore.token && !userStore.userId) {
    try {
      await userStore.getCurrentUser()
    } catch (error) {
      // 仅在认证失效时清除 token；临时网络错误不应把用户踢回登录页
      console.error('获取用户信息失败:', error)
      const status = Number(error?.status)
      if (status === 401 || status === 403) {
        userStore.logout()
      }
    }
  }

  const isLoggedIn = userStore.isLoggedIn
  const isAdmin = userStore.isAdmin

  // 如果路由需要认证但用户未登录
  if (requiresAuth && !isLoggedIn) {
    // 保存尝试访问的路径，登录后跳转
    sessionStorage.setItem('redirect', to.fullPath)
    next('/')
    return
  }

  // 如果路由需要管理员权限但用户不是管理员
  if (requiresAdmin && !isAdmin) {
    // 普通用户跳转到知识库页面
    next('/knowledge')
    return
  }

  // 如果用户已登录但访问登录页（首页），根据用户角色跳转
  if (to.path === '/' && isLoggedIn) {
    if (isAdmin) {
      next('/database')
    } else {
      next('/knowledge')
    }
    return
  }

  // 其他情况正常导航
  next()
})

export default router
