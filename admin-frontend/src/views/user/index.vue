<template>
  <div class="user-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
        </div>
      </template>

      <!-- 搜索和筛选区域 -->
      <div class="filter-container">
        <el-input
          v-model="queryParams.nickname"
          placeholder="请输入用户昵称"
          style="width: 200px;"
          class="filter-item"
          @keyup.enter="handleSearch"
        />

        <el-select
          v-model="queryParams.is_blocked"
          placeholder="账户状态"
          clearable
          style="width: 130px"
          class="filter-item"
        >
          <el-option label="正常" :value="false" />
          <el-option label="已封禁" :value="true" />
        </el-select>

        <el-button
          type="primary"
          :icon="Search"
          class="filter-item"
          @click="handleSearch"
        >
          搜索
        </el-button>

        <el-button
          :icon="Refresh"
          class="filter-item"
          @click="resetQuery"
        >
          重置
        </el-button>
      </div>

      <!-- 用户表格 -->
      <el-table
        v-loading="loading"
        :data="userList"
        style="width: 100%;"
        border
      >
        <el-table-column
          type="index"
          width="50"
          align="center"
        />

        <el-table-column
          prop="id"
          label="ID"
          width="80"
          align="center"
        />

        <el-table-column
          label="头像"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-avatar
              :size="40"
              :src="row.avatar_url"
              @error="() => true"
            >
              {{ row.nickname.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>

        <el-table-column
          prop="nickname"
          label="用户昵称"
          min-width="120"
          align="center"
        />

        <el-table-column
          prop="openid"
          label="OpenID"
          width="120"
          align="center"
          :show-overflow-tooltip="true"
        />

        <el-table-column
          prop="unionid"
          label="UnionID"
          width="120"
          align="center"
          :show-overflow-tooltip="true"
        />

        <el-table-column
          prop="gender"
          label="性别"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            {{ row.gender === 1 ? '男' : (row.gender === 2 ? '女' : '未知') }}
          </template>
        </el-table-column>

        <el-table-column
          label="地区"
          width="150"
          align="center"
          :show-overflow-tooltip="true"
        >
          <template #default="{ row }">
            {{ [row.country, row.province, row.city].filter(Boolean).join(' / ') || '未知' }}
          </template>
        </el-table-column>

        <el-table-column
          prop="credits"
          label="积分"
          width="100"
          align="center"
        />

        <el-table-column
          prop="is_blocked"
          label="状态"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.is_blocked ? 'danger' : 'success'"
            >
              {{ row.is_blocked ? '已封禁' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="created_at"
          label="注册时间"
          width="180"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="updated_at"
          label="更新时间"
          width="180"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="last_login_time"
          label="最后登录时间"
          width="180"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.last_login_time) }}
          </template>
        </el-table-column>

        <el-table-column
          label="操作"
          fixed="right"
          width="240"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="View"
              @click="handleDetail(row)"
            >
              查看
            </el-button>

            <el-button
              :type="row.is_blocked ? 'success' : 'danger'"
              link
              :icon="row.is_blocked ? 'Unlock' : 'Lock'"
              @click="handleBlockToggle(row)"
            >
              {{ row.is_blocked ? '解封' : '封禁' }}
            </el-button>

            <el-button
              type="primary"
              link
              :icon="Wallet"
              @click="handleAdjustCredits(row)"
            >
              调整积分
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 调整积分弹窗 -->
    <el-dialog
      v-model="creditDialogVisible"
      title="调整积分"
      width="500px"
    >
      <div v-if="selectedUser" class="credit-dialog-content">
        <p class="user-info-text">
          用户: <span class="value">{{ selectedUser.nickname }}</span>
          <br>
          当前积分: <span class="value">{{ selectedUser.credits }}</span>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, View, Wallet, Lock, Unlock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { getUsers, blockUser, adjustUserCredits } from '@/api/user'
import type { User } from '@/api/user'

const router = useRouter()

// 加载状态
const loading = ref(false)
const creditSubmitting = ref(false)

// 用户列表数据
const userList = ref<User[]>([])
const total = ref(0)

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  skip: 0,
  nickname: '',
  is_blocked: undefined as boolean | undefined
})

// 积分调整对话框
const creditDialogVisible = ref(false)
const selectedUser = ref<User | null>(null)
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

// 获取用户列表
const getUserList = async () => {
  try {
    loading.value = true
    queryParams.skip = (queryParams.page - 1) * queryParams.limit

    const res = await getUsers(queryParams)
    console.log('用户API返回数据:', res) // 调试日志

    // 处理数组形式的响应
    if (Array.isArray(res)) {
      userList.value = res
      total.value = res.length
    }
    // 处理分页格式的响应 {items: [], total: 0}
    else if (res && typeof res === 'object' && 'items' in res && 'total' in res) {
      userList.value = res.items || []
      total.value = res.total || 0
    }
    // 处理可能的其他格式响应
    else if (res && typeof res === 'object') {
      // 尝试将对象转为数组
      const items = Object.values(res).filter(item =>
        typeof item === 'object' && item !== null && 'id' in item
      ) as User[]

      if (items.length > 0) {
        userList.value = items
        total.value = items.length
      } else {
        userList.value = []
        total.value = 0
      }
    } else {
      userList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    userList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 搜索按钮点击事件
const handleSearch = () => {
  queryParams.page = 1
  getUserList()
}

// 重置查询条件
const resetQuery = () => {
  queryParams.nickname = ''
  queryParams.is_blocked = undefined
  queryParams.page = 1
  getUserList()
}

// 查看用户详情
const handleDetail = (row: User) => {
  router.push(`/user/${row.id}`)
}

// 处理封禁/解封用户
const handleBlockToggle = (row: User) => {
  const isBlocked = row.is_blocked
  const actionText = isBlocked ? '解封' : '封禁'

  ElMessageBox.confirm(
    `确定要${actionText}用户 "${row.nickname}" 吗？`,
    `${actionText}用户`,
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await blockUser(row.id, !isBlocked)
      row.is_blocked = !isBlocked
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
const handleAdjustCredits = (row: User) => {
  selectedUser.value = row
  creditForm.type = 'increase'
  creditForm.amount = 10
  creditForm.description = ''
  creditDialogVisible.value = true
}

// 提交积分调整
const submitCreditAdjustment = () => {
  if (!selectedUser.value) return

  creditFormRef.value?.validate(async (valid) => {
    if (valid) {
      try {
        creditSubmitting.value = true

        // 计算实际积分变动量（增加为正，减少为负）
        const amount = creditForm.type === 'increase'
          ? Math.abs(creditForm.amount)
          : -Math.abs(creditForm.amount)

        const res = await adjustUserCredits(selectedUser.value.id, {
          amount,
          type: 'admin_adjustment',
          description: creditForm.description
        })

        // 更新本地数据
        if (selectedUser.value) {
          selectedUser.value.credits = res.balance
          // 更新列表中的数据
          const user = userList.value.find(u => u.id === selectedUser.value?.id)
          if (user) {
            user.credits = res.balance
          }
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

// 分页页码改变
const handleCurrentChange = (page: number) => {
  queryParams.page = page
  getUserList()
}

// 分页大小改变
const handleSizeChange = (size: number) => {
  queryParams.limit = size
  queryParams.page = 1
  getUserList()
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

// 页面加载时获取用户列表
onMounted(() => {
  getUserList()
})
</script>

<style scoped lang="scss">
.user-container {
  width: 100%;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .filter-container {
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 20px;
    gap: 10px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .user-info {
    display: flex;
    align-items: center;

    .nickname {
      margin-left: 10px;
    }
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
