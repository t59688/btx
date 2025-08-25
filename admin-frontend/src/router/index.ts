import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/login/index.vue'),
      meta: { title: '登录', requiresAuth: false }
    },
    {
      path: '/',
      name: 'layout',
      component: () => import('@/views/layout/index.vue'),
      redirect: '/dashboard',
      meta: { requiresAuth: true },
      children: [
    {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/dashboard/index.vue'),
          meta: { title: '仪表盘', icon: 'DataBoard', requiresAuth: true }
        },
        {
          path: 'user',
          name: 'user',
          component: () => import('@/views/user/index.vue'),
          meta: { title: '用户管理', icon: 'User', requiresAuth: true }
        },
        {
          path: 'user/:id',
          name: 'userDetail',
          component: () => import('@/views/user/detail.vue'),
          meta: { title: '用户详情', requiresAuth: true, hidden: true },
          props: true
        },
        {
          path: 'style',
          name: 'style',
          component: () => import('@/views/style/index.vue'),
          meta: { title: '风格管理', icon: 'Picture', requiresAuth: true }
        },
        {
          path: 'category',
          name: 'category',
          component: () => import('@/views/category/index.vue'),
          meta: { title: '分类管理', icon: 'Files', requiresAuth: true }
        },
        {
          path: 'artwork',
          name: 'artwork',
          component: () => import('@/views/artwork/index.vue'),
          meta: { title: '作品管理', icon: 'PictureRounded', requiresAuth: true }
        },
        {
          path: 'card-key',
          name: 'cardKey',
          component: () => import('@/views/card-key/CardKeyList.vue'),
          meta: { title: '卡密管理', icon: 'Ticket', requiresAuth: true }
        },
        {
          path: 'product',
          name: 'product',
          component: () => import('@/views/product/index.vue'),
          meta: { title: '商品管理', icon: 'GoodsFilled', requiresAuth: true }
        },
        {
          path: 'order',
          name: 'order',
          component: () => import('@/views/order/index.vue'),
          meta: { title: '订单管理', icon: 'List', requiresAuth: true }
        },
        {
          path: 'config',
          name: 'config',
          component: () => import('@/views/config/index.vue'),
          meta: { title: '系统配置', icon: 'Setting', requiresAuth: true }
        }
      ]
    },
    // 404页面
    {
      path: '/:pathMatch(.*)*',
      name: 'notFound',
      component: () => import('@/views/error/404.vue'),
      meta: { title: '404', requiresAuth: false }
    }
  ]
})

// 导航守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || 'AI'} - 管理系统`

  // 检查该路由是否需要登录权限
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 获取存储的token
    const token = localStorage.getItem('token')

    // 如果没有token，跳转到登录页
    if (!token) {
      next({
        path: '/login',
        query: { redirect: to.fullPath } // 将要跳转的路由作为参数，登录成功后跳转到该路由
      })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
