<template>
  <div class="app-wrapper">
    <!-- 侧边栏 -->
    <div class="sidebar-container" :class="{ 'is-collapse': isCollapse }">
      <div class="logo-container">
        <img src="@/assets/logo.png" alt="Logo" class="logo-img" />
        <h1 v-if="!isCollapse" class="logo-text">AI绘画管理</h1>
      </div>
      <el-scrollbar>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          :unique-opened="true"
          :collapse-transition="false"
          mode="vertical"
          router
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataLine /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <el-menu-item index="/user">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>

          <el-menu-item index="/artwork">
            <el-icon><Picture /></el-icon>
            <template #title>作品管理</template>
          </el-menu-item>

          <el-menu-item index="/style">
            <el-icon><Brush /></el-icon>
            <template #title>风格管理</template>
          </el-menu-item>

          <el-menu-item index="/config">
            <el-icon><Setting /></el-icon>
            <template #title>系统配置</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </div>

    <!-- 主容器 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <div class="navbar">
        <div class="left-area">
          <el-icon class="fold-icon" @click="toggleSidebar">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <breadcrumb class="breadcrumb" />
        </div>
        <div class="right-area">
          <el-dropdown trigger="click">
            <div class="avatar-wrapper">
              <el-avatar :size="32" :src="avatarUrl" />
              <span class="user-name">{{ userName }}</span>
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DataLine,
  User,
  Picture,
  Brush,
  Setting,
  Fold,
  Expand,
  CaretBottom,
  SwitchButton
} from '@element-plus/icons-vue'

// 组件导入
const Breadcrumb = {
  render() {
    return h('div', { class: 'breadcrumb-container' }, '首页')
  }
}

// 侧边栏折叠状态
const isCollapse = ref(false)
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

// 当前活动菜单
const route = useRoute()
const activeMenu = computed(() => {
  return route.path
})

// 用户信息
const userName = ref('管理员')
const avatarUrl = ref('https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')

// 登出
const router = useRouter()
const handleLogout = () => {
  // 清除登录信息
  localStorage.removeItem('token')

  // 跳转到登录页
  router.push('/login')
}
</script>

<style scoped lang="scss">
.app-wrapper {
  position: relative;
  height: 100%;
  width: 100%;
  display: flex;
}

// 侧边栏样式
.sidebar-container {
  width: 210px;
  height: 100%;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background-color: #304156;
  transition: width 0.28s;
  z-index: 1001;
  overflow: hidden;

  &.is-collapse {
    width: 64px;
  }

  .logo-container {
    height: 50px;
    padding: 10px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #2b3649;

    .logo-img {
      width: 32px;
      height: 32px;
      margin-right: 10px;
    }

    .logo-text {
      color: #fff;
      font-size: 16px;
      font-weight: bold;
      margin: 0;
      white-space: nowrap;
    }
  }
}

// 主容器样式
.main-container {
  min-height: 100%;
  margin-left: 210px;
  position: relative;
  transition: margin-left 0.28s;
  width: calc(100% - 210px);

  .sidebar-container.is-collapse + & {
    margin-left: 64px;
    width: calc(100% - 64px);
  }
}

// 顶部导航样式
.navbar {
  height: 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  background-color: #fff;

  .left-area {
    display: flex;
    align-items: center;

    .fold-icon {
      font-size: 20px;
      cursor: pointer;
      margin-right: 15px;
    }

    .breadcrumb {
      margin-left: 8px;
    }
  }

  .right-area {
    .avatar-wrapper {
      display: flex;
      align-items: center;
      cursor: pointer;

      .user-name {
        margin: 0 5px;
        color: #606266;
      }
    }
  }
}

// 主内容区样式
.app-main {
  min-height: calc(100vh - 50px);
  padding: 15px;
  position: relative;
  overflow: hidden;
  background-color: #f0f2f5;
}
</style>
