import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/pages/Home.vue')
      },
      {
        path: 'task/:id',
        name: 'Task',
        component: () => import('@/pages/TaskDetail.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 初始化认证状态（每次路由切换时都检查）
  userStore.initAuth()

  // 获取路由的认证要求（默认需要认证，除非明确设置为 false）
  const requiresAuth = to.meta.requiresAuth !== false

  // 如果路由需要认证但用户未登录，重定向到登录页
  if (requiresAuth && !userStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 如果已登录用户访问登录/注册页，重定向到首页
  if ((to.name === 'Login' || to.name === 'Register') && userStore.isAuthenticated) {
    next({ name: 'Home' })
    return
  }

  // 允许访问
  next()
})

export default router

