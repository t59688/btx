<template>
  <div class="user-detail-container" v-loading="loading">
    <el-card class="back-card">
      <el-button type="primary" plain :icon="Back" @click="goBack">返回用户列表</el-button>
    </el-card>

    <el-row :gutter="20" v-if="userInfo">
      <!-- 用户基本信息 -->
      <el-col :span="8">
        <el-card class="user-info-card">
          <template #header>
            <div class="card-header">
              <span>用户信息</span>
              <div class="header-actions">
                <el-button
                  :type="userInfo.is_blocked ? 'success' : 'danger'"
                  plain
                  :icon="userInfo.is_blocked ? 'Unlock' : 'Lock'"
                  @click="handleBlockToggle"
                >
                  {{ userInfo.is_blocked ? '解封' : '封禁' }}
                </el-button>

                <el-button
                  type="primary"
                  plain
                  :icon="Wallet"
                  @click="handleAdjustCredits"
                >
                  调整积分
                </el-button>
              </div>
            </div>
          </template>

          <div class="user-profile">
            <div class="user-avatar">
              <el-avatar
                :size="100"
                :src="userInfo.avatar_url"
                @error="() => true"
              >
                {{ userInfo.nickname?.charAt(0) }}
              </el-avatar>
            </div>

            <div class="user-meta">
              <div class="meta-item">
                <span class="meta-label">用户ID:</span>
                <span class="meta-value">{{ userInfo.id }}</span>
              </div>

              <div class="meta-item">
                <span class="meta-label">昵称:</span>
                <span class="meta-value">{{ userInfo.nickname }}</span>
              </div>

              <div class="meta-item">
                <span class="meta-label">积分:</span>
                <span class="meta-value">{{ userInfo.credits }}</span>
              </div>

              <div class="meta-item">
                <span class="meta-label">状态:</span>
                <span class="meta-value">
                  <el-tag :type="userInfo.is_blocked ? 'danger' : 'success'">
                    {{ userInfo.is_blocked ? '已封禁' : '正常' }}
                  </el-tag>
                </span>
              </div>

              <div class="meta-item">
                <span class="meta-label">OpenID:</span>
                <span class="meta-value">{{ userInfo.openid || '暂无' }}</span>
              </div>

              <div class="meta-item">
                <span class="meta-label">注册时间:</span>
                <span class="meta-value">{{ formatDateTime(userInfo.created_at) }}</span>
              </div>

              <div class="meta-item">
                <span class="meta-label">最后登录:</span>
                <span class="meta-value">{{ formatDateTime(userInfo.last_login_time) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 积分记录与作品 -->
      <el-col :span="16">
        <el-tabs>
          <!-- 积分记录 -->
          <el-tab-pane label="积分记录">
            <el-card>
              <el-table
                :data="creditRecords"
                style="width: 100%"
                v-loading="creditLoading"
              >
                <el-table-column prop="id" label="ID" width="80" align="center" />

                <el-table-column prop="type" label="类型" width="150">
                  <template #default="{ row }">
                    <el-tag :type="getCreditTypeTag(row.type)">
                      {{ getCreditTypeLabel(row.type) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="amount" label="变动数量" width="120">
                  <template #default="{ row }">
                    <span :class="{ 'text-success': row.amount > 0, 'text-danger': row.amount < 0 }">
                      {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
                    </span>
                  </template>
                </el-table-column>

                <el-table-column prop="balance" label="余额" width="100" />

                <el-table-column prop="description" label="说明" min-width="150" show-overflow-tooltip />

                <el-table-column prop="created_at" label="时间" width="180">
                  <template #default="{ row }">
                    {{ formatDateTime(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>

              <!-- 积分记录分页 -->
              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="creditQuery.page"
                  v-model:page-size="creditQuery.per_page"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next"
                  :total="creditTotal"
                  @size-change="handleCreditSizeChange"
                  @current-change="handleCreditPageChange"
                />
              </div>
            </el-card>
          </el-tab-pane>

          <!-- 作品列表 -->
          <el-tab-pane label="作品列表">
            <el-card>
              <el-table
                :data="artworks"
                style="width: 100%"
                v-loading="artworkLoading"
              >
                <el-table-column prop="id" label="ID" width="80" align="center" />

                <el-table-column label="图片" width="150">
                  <template #default="{ row }">
                    <el-image
                      style="width: 80px; height: 80px"
                      :src="row.result_image_url || row.source_image_url"
                      fit="cover"
                      :preview-src-list="[row.source_image_url, row.result_image_url].filter(Boolean)"
                    />
                  </template>
                </el-table-column>

                <el-table-column prop="style.name" label="风格" width="120" />

                <el-table-column prop="status" label="状态" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getStatusTag(row.status)">
                      {{ getStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="is_public" label="是否公开" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.is_public ? 'success' : 'info'">
                      {{ row.is_public ? '公开' : '私密' }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="created_at" label="创建时间" width="180">
                  <template #default="{ row }">
                    {{ formatDateTime(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>

              <!-- 作品分页 -->
              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="artworkQuery.page"
                  v-model:page-size="artworkQuery.limit"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next"
                  :total="artworkTotal"
                  @size-change="handleArtworkSizeChange"
                  @current-change="handleArtworkPageChange"
                />
              </div>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>

    <!-- 积分调整弹窗 -->
    <el-dialog
      v-model="creditDialogVisible"
      title="调整积分"
      width="500px"
    >
      <div v-if="userInfo" class="credit-dialog-content">
        <p class="user-info-text">
          用户: <span class="value">{{ userInfo.nickname }}</span>
          <br>
          当前积分: <span class="value">{{ userInfo.credits }}</span>
        </p>

        <el-form
          ref="creditFormRef"
          :model="creditForm"
          :rules="creditRules"
          label-width="100px"
        >
          <el-form-item label="调整类型" prop="type">
            <el-radio-group v-model="creditForm.type">
              <el-radio-button label="increase">增加</el-radio-button>
              <el-radio-button label="decrease">减少</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="积分数量" prop="amount">
            <el-input-number
              v-model="creditForm.amount"
              :min="1"
              :max="1000"
              :precision="0"
            />
          </el-form-item>

          <el-form-item label="调整说明" prop="description">
            <el-input
              v-model="creditForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入调整原因"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="creditDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="creditSubmitting" @click="submitCreditAdjustment">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Wallet, Lock, Unlock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { getUserDetail, blockUser, adjustUserCredits, getUserCreditRecords, type User, type CreditRecord, type PaginatedResponse } from '@/api/user'
import { getArtworks, type Artwork } from '@/api/artwork'

const route = useRoute()
const router = useRouter()
const userId = Number(route.params.id)

// 加载状态
const loading = ref(false)
const creditLoading = ref(false)
const artworkLoading = ref(false)
const creditSubmitting = ref(false)

// 用户信息
const userInfo = ref<User | null>(null)

// 积分记录
const creditRecords = ref<CreditRecord[]>([])
const creditTotal = ref(0)
const creditQuery = reactive({
  page: 1,
  per_page: 10,
  user_id: userId
})

// 作品列表
const artworks = ref<Artwork[]>([])
const artworkTotal = ref(0)
const artworkQuery = reactive({
  page: 1,
  limit: 10,
  user_id: userId
})

// 积分调整弹窗
const creditDialogVisible = ref(false)
const creditFormRef = ref<FormInstance>()
const creditForm = reactive({
  type: 'increase',
  amount: 10,
  description: ''
})

// 表单验证规则
const creditRules: FormRules = {
  amount: [
    { required: true, message: '请输入积分数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '积分数量必须大于0', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入调整说明', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 获取用户详情
const getUserInfo = async () => {
  try {
    loading.value = true
    const response = await getUserDetail(userId)
    // 解析API响应数据
    userInfo.value = response as unknown as User

    // 获取积分记录和作品
    fetchCreditRecords()
    fetchUserArtworks()
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  } finally {
    loading.value = false
  }
}

// 获取积分记录
const fetchCreditRecords = async () => {
  try {
    creditLoading.value = true
    const response = await getUserCreditRecords(userId, {
      page: creditQuery.page,
      per_page: creditQuery.per_page
    })

    // 处理API响应
    const res = response as unknown as PaginatedResponse<CreditRecord>
    if (res && typeof res === 'object') {
      creditRecords.value = res.items || []
      creditTotal.value = res.total || 0
    } else {
      creditRecords.value = []
      creditTotal.value = 0
    }
  } catch (error) {
    console.error('获取积分记录失败:', error)
    creditRecords.value = []
    creditTotal.value = 0
  } finally {
    creditLoading.value = false
  }
}

// 获取用户作品
const fetchUserArtworks = async () => {
  try {
    artworkLoading.value = true
    const res = await getArtworks({
      user_id: userId,
      skip: (artworkQuery.page - 1) * artworkQuery.limit,
      limit: artworkQuery.limit
    })
    artworks.value = res.items || []
    artworkTotal.value = res.total || 0
  } catch (error) {
    console.error('获取用户作品失败:', error)
  } finally {
    artworkLoading.value = false
  }
}

// 封禁/解封用户
const handleBlockToggle = () => {
  if (!userInfo.value) return

  const isBlocked = userInfo.value.is_blocked
  const actionText = isBlocked ? '解封' : '封禁'

  ElMessageBox.confirm(
    `确定要${actionText}用户 "${userInfo.value.nickname}" 吗？`,
    `${actionText}用户`,
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      if (!userInfo.value) return

      await blockUser(userInfo.value.id, !isBlocked)
      userInfo.value.is_blocked = !isBlocked

      ElMessage({
        type: 'success',
        message: `${actionText}成功`
      })
    } catch (error) {
      console.error(`${actionText}失败:`, error)
    }
  }).catch(() => {})
}

// 处理调整积分
const handleAdjustCredits = () => {
  creditForm.type = 'increase'
  creditForm.amount = 10
  creditForm.description = ''
  creditDialogVisible.value = true
}

// 提交积分调整
const submitCreditAdjustment = () => {
  if (!userInfo.value) return

  creditFormRef.value?.validate(async (valid) => {
    if (valid) {
      try {
        creditSubmitting.value = true

        // 计算实际积分变动量（增加为正，减少为负）
        const amount = creditForm.type === 'increase'
          ? Math.abs(creditForm.amount)
          : -Math.abs(creditForm.amount)

        if (!userInfo.value) return

        const response = await adjustUserCredits(userInfo.value.id, {
          amount,
          type: 'admin_adjustment',
          description: creditForm.description
        })

        // 更新本地数据
        const res = response as unknown as { balance: number }
        if (userInfo.value && res && typeof res === 'object' && 'balance' in res) {
          userInfo.value.credits = res.balance

          // 更新积分记录
          fetchCreditRecords()
        }

        ElMessage({
          type: 'success',
          message: '积分调整成功'
        })

        creditDialogVisible.value = false
      } catch (error) {
        console.error('积分调整失败:', error)
      } finally {
        creditSubmitting.value = false
      }
    }
  })
}

// 分页处理 - 积分记录
const handleCreditPageChange = (page: number) => {
  creditQuery.page = page
  fetchCreditRecords()
}

const handleCreditSizeChange = (size: number) => {
  creditQuery.per_page = size
  creditQuery.page = 1
  fetchCreditRecords()
}

// 分页处理 - 作品
const handleArtworkPageChange = (page: number) => {
  artworkQuery.page = page
  fetchUserArtworks()
}

const handleArtworkSizeChange = (size: number) => {
  artworkQuery.limit = size
  artworkQuery.page = 1
  fetchUserArtworks()
}

// 返回用户列表
const goBack = () => {
  router.push('/user')
}

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '暂无'

  const date = new Date(dateString)

  // 处理无效日期
  if (isNaN(date.getTime())) return '暂无'

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

// 获取积分类型标签
const getCreditTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    'admin_adjustment': '管理员调整',
    'artwork_creation': '创建作品',
    'registration': '注册奖励',
    'ad_watch': '广告观看',
    'daily_login': '每日登录'
  }
  return typeMap[type] || type
}

// 获取积分类型标签样式
const getCreditTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    'admin_adjustment': 'primary',
    'artwork_creation': 'danger',
    'registration': 'success',
    'ad_watch': 'warning',
    'daily_login': 'info'
  }
  return tagMap[type] || ''
}

// 获取作品状态标签
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取作品状态标签样式
const getStatusTag = (status: string) => {
  const tagMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return tagMap[status] || ''
}

// 组件挂载时获取数据
onMounted(() => {
  if (userId) {
    getUserInfo()
  } else {
    ElMessage.error('用户ID无效')
    router.push('/user')
  }
})
</script>

<style scoped lang="scss">
.user-detail-container {
  .back-card {
    margin-bottom: 20px;
  }

  .user-info-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 10px;
      }
    }

    .user-profile {
      .user-avatar {
        text-align: center;
        margin-bottom: 20px;
      }

      .user-meta {
        .meta-item {
          margin-bottom: 10px;
          display: flex;

          .meta-label {
            font-weight: bold;
            width: 100px;
          }

          .meta-value {
            flex: 1;
          }
        }
      }
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .text-success {
    color: #67c23a;
  }

  .text-danger {
    color: #f56c6c;
  }

  .credit-dialog-content {
    .user-info-text {
      margin-bottom: 20px;

      .value {
        font-weight: bold;
      }
    }
  }
}
</style>
