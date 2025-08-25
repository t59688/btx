<template>
  <div class="layout-container">
    <el-container class="layout-container-box">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
        <div class="logo-container">
          <img src="@/assets/logo.png" alt="Logo" class="logo" />
          <span v-show="!isCollapse" class="logo-text">管理系统</span>
        </div>

        <!-- 侧边导航菜单 -->
        <el-menu
          :default-active="activeMenu"
          router
          class="layout-menu"
          :collapse="isCollapse"
          background-color="#001529"
          text-color="#fff"
          active-text-color="#ffd04b"
        >
          <el-menu-item v-for="route in routes" :key="route.path" :index="route.path" v-show="!route.meta?.hidden">
            <el-icon><component :is="route.meta?.icon" /></el-icon>
            <template #title>{{ route.meta?.title }}</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container class="layout-main">
        <!-- 头部 -->
        <el-header class="layout-header">
          <div class="header-left">
            <el-icon class="collapse-btn" @click="toggleCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
            <!-- 面包屑导航 -->
            <el-breadcrumb>
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
                {{ item.meta.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <el-dropdown trigger="click" @command="handleCommand">
              <span class="admin-name">
                {{ adminInfo?.username }}
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 内容区 -->
        <el-main class="layout-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <keep-alive>
                <component :is="Component" />
              </keep-alive>
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowDown, Fold, Expand } from '@element-plus/icons-vue'
import type { RouteRecordRaw } from 'vue-router'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 获取管理员信息
const adminInfo = computed(() => authStore.adminInfo)

// 获取路由（用于侧边栏菜单）
const routes = computed(() => {
  const mainRoutes = router.options.routes.find(r => r.path === '/')
  return mainRoutes?.children || []
})

// 控制侧边栏折叠状态
const isCollapse = ref(false)
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 当前激活的菜单项
const activeMenu = computed(() => {
  const { path } = route
  // 如果是用户详情页，激活用户管理菜单
  if (path.indexOf('/user/') === 0) {
    return '/user'
  }
  return path
})

// 面包屑导航
const breadcrumbs = computed(() => {
  const res: any[] = []
  const { matched } = route

  // 首先添加Dashboard
  if (matched[0]?.path === '/' && matched[1]?.path !== 'dashboard') {
    res.push({
      path: '/dashboard',
      meta: { title: '首页' }
    })
  }

  // 添加当前路由及其父路由
  matched.forEach(item => {
    if (item.meta?.title && item.path !== '/') {
      res.push(item)
    }
  })

  return res
})

// 下拉菜单命令处理
const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
  }
}

// 页面加载时获取管理员信息
onMounted(() => {
  // 如果已登录但没有管理员信息，则获取
  if (authStore.token && !authStore.adminInfo) {
    authStore.getAdminInfoAction()
  }
})
</script>

<style scoped lang="scss">
.layout-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;

  .layout-container-box {
    height: 100vh;
  }

  .layout-aside {
    background-color: #001529;
    transition: width 0.3s;
    overflow-y: auto;
    overflow-x: hidden;

    .logo-container {
      height: 60px;
      padding: 12px 20px;
      display: flex;
      align-items: center;
      justify-content: center;

      .logo {
        height: 32px;
        width: 32px;
        margin-right: 12px;
      }

      .logo-text {
        color: white;
        font-size: 16px;
        font-weight: bold;
        white-space: nowrap;
      }
    }

    .layout-menu {
      border-right: none;
      /* 去掉菜单的字体大小限制 */
      --el-menu-item-font-size: 15px;
      height: calc(100vh - 60px);
    }
  }

  .layout-main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 100%;

    .layout-header {
      background-color: #fff;
      box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
      padding: 0 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;

      .header-left {
        display: flex;
        align-items: center;

        .collapse-btn {
          margin-right: 20px;
          font-size: 22px;
          cursor: pointer;
        }
      }

      .header-right {
        .admin-name {
          cursor: pointer;
          display: flex;
          align-items: center;
          font-size: 15px;
        }
      }
    }

    .layout-content {
      padding: 20px;
      overflow-y: auto;
      background-color: #f0f2f5;
      box-sizing: border-box;
      /* 最小宽度确保内容不会过度压缩 */
      min-width: 800px;
      /* 在宽屏上提供最大宽度和居中效果 */
      max-width: 100%;
      margin: 0 auto;
      flex: 1;
      width: 100%;
    }
  }
}

/* 响应式设计：大屏幕优化 */
@media (min-width: 1600px) {
  .layout-main .layout-content {
    padding: 25px 30px;
  }
}

/* 极宽屏幕优化 */
@media (min-width: 2000px) {
  .layout-main .layout-content {
    padding: 30px 40px;
    max-width: 100%; /* 修改为100%，占满整个空间 */
    margin: 0 auto;
  }
}

// 路由过渡动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
