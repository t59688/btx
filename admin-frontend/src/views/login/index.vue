<template>
  <div class="login-container">
    <div class="login-left">
      <div class="login-content">
        <div class="login-header">
          <img src="@/assets/logo.png" alt="Logo" class="logo-img" />
          <h1 class="title">AI管理系统</h1>
          <p class="subtitle">专业的后台管理平台</p>
        </div>
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="login-card-header">
          <h2 class="title">系统登录</h2>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          auto-complete="on"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名"
              prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              placeholder="密码"
              prefix-icon="Lock"
              :type="passwordVisible ? 'text' : 'password'"
            >
              <template #suffix>
                <el-icon
                  class="password-icon"
                  @click="passwordVisible = !passwordVisible"
                >
                  <View v-if="passwordVisible" />
                  <Hide v-else />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item class="login-button-container">
            <el-button
              :loading="loading"
              type="primary"
              class="login-button"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>

        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, View, Hide } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance } from 'element-plus'

// 路由
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 密码可见性
const passwordVisible = ref(false)

// 加载状态
const loading = computed(() => authStore.loading)

// 表单引用
const loginFormRef = ref<FormInstance | null>(null)

// 登录方法
const handleLogin = () => {
  if (!loginFormRef.value) return

  loginFormRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      return
    }

    try {
      await authStore.loginAction(loginForm)

      // 如果存在重定向地址，则跳转到重定向地址
      const redirect = route.query.redirect as string
      if (redirect) {
        router.push(redirect)
      }
    } catch (error) {
      console.error('登录失败:', error)
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;

  .login-left {
    flex: 1;
    background-color: #001529;
    background-image: linear-gradient(135deg, #002140 0%, #001528 100%);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-size: cover;
      background-position: center;
      opacity: 0.3;
    }

    .login-content {
      position: relative;
      z-index: 2;
      width: 100%;
      max-width: 800px;
      text-align: center;

      .login-header {
        .logo-img {
          width: 120px;
          height: 120px;
          margin-bottom: 30px;
        }

        .title {
          font-size: 42px;
          color: #ffffff;
          margin: 0 0 20px;
          letter-spacing: 1px;
          text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .subtitle {
          font-size: 22px;
          color: rgba(255, 255, 255, 0.8);
          margin: 0;
        }
      }
    }
  }

  .login-right {
    width: 500px;
    background-color: #f0f2f5;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    overflow-y: auto;

    .login-card {
      width: 100%;
      padding: 40px;
      background: #ffffff;
      border-radius: 8px;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);

      .login-card-header {
        text-align: center;
        margin-bottom: 40px;

        .title {
          font-size: 28px;
          color: #303133;
          margin: 0;
        }
      }

      .login-form {
        .el-form-item {
          margin-bottom: 24px;
        }

        .password-icon {
          cursor: pointer;
          font-size: 18px;
        }

        .login-button-container {
          margin-top: 40px;

          .login-button {
            width: 100%;
            height: 48px;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
          }
        }

        .login-tips {
          margin-top: 20px;
          font-size: 14px;
          color: #999;
          display: flex;
          justify-content: space-between;
        }
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 992px) {
  .login-container {
    flex-direction: column;

    .login-left {
      flex: none;
      height: 30%;
      min-height: 200px;
      padding: 20px;

      .login-content {
        .login-header {
          .logo-img {
            width: 80px;
            height: 80px;
            margin-bottom: 15px;
          }

          .title {
            font-size: 28px;
            margin-bottom: 10px;
          }

          .subtitle {
            font-size: 16px;
          }
        }
      }
    }

    .login-right {
      width: 100%;
      height: 70%;
      padding: 20px;

      .login-card {
        padding: 30px;
        max-height: 100%;

        .login-card-header {
          margin-bottom: 20px;

          .title {
            font-size: 24px;
          }
        }

        .login-form {
          .el-form-item {
            margin-bottom: 16px;
          }

          .login-button-container {
            margin-top: 30px;
          }
        }
      }
    }
  }
}

/* 低高度屏幕适配 */
@media (max-height: 700px) {
  .login-container {
    .login-left {
      .login-content {
        .login-header {
          .logo-img {
            width: 80px;
            height: 80px;
            margin-bottom: 15px;
          }

          .title {
            font-size: 32px;
            margin-bottom: 10px;
          }

          .subtitle {
            font-size: 18px;
          }
        }
      }
    }

    .login-right {
      .login-card {
        padding: 30px;

        .login-card-header {
          margin-bottom: 20px;
        }

        .login-form {
          .el-form-item {
            margin-bottom: 16px;
          }

          .login-button-container {
            margin-top: 25px;
          }
        }
      }
    }
  }
}

/* 宽屏适配 */
@media (min-width: 1600px) {
  .login-container {
    .login-left {
      flex: 2;
      .login-content {
        max-width: 1200px;

        .login-header {
          .logo-img {
            width: 160px;
            height: 160px;
            margin-bottom: 40px;
          }

          .title {
            font-size: 60px;
            margin-bottom: 30px;
          }

          .subtitle {
            font-size: 32px;
          }
        }
      }
    }

    .login-right {
      width: 650px;
      padding: 60px;

      .login-card {
        padding: 60px;

        .login-card-header {
          margin-bottom: 50px;

          .title {
            font-size: 32px;
          }
        }

        .login-form {
          .el-form-item {
            margin-bottom: 30px;
          }

          .login-button-container {
            margin-top: 50px;

            .login-button {
              height: 54px;
              font-size: 18px;
            }
          }

          .login-tips {
            margin-top: 30px;
            font-size: 16px;
          }
        }
      }
    }
  }
}

/* 超宽屏适配 */
@media (min-width: 2000px) {
  .login-container {
    .login-left {
      flex: 3;
      .login-content {
        max-width: 1500px;

        .login-header {
          .logo-img {
            width: 200px;
            height: 200px;
          }

          .title {
            font-size: 72px;
          }

          .subtitle {
            font-size: 38px;
          }
        }
      }
    }

    .login-right {
      width: 750px;

      .login-card {
        padding: 80px;
      }
    }
  }
}
</style>
