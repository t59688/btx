<template>
  <div class="config-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">系统配置</span>
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增配置</el-button>
        </div>
      </template>

      <!-- 搜索和筛选区域 -->
      <div class="filter-container">
        <el-input
          v-model="searchPrefix"
          placeholder="请输入配置前缀"
          class="filter-item"
          @keyup.enter="handleSearch"
        />

        <el-button type="primary" :icon="Search" class="filter-item" @click="handleSearch">
          搜索
        </el-button>

        <el-button :icon="Refresh" class="filter-item" @click="resetQuery"> 重置 </el-button>
      </div>

      <!-- 配置表格 -->
      <el-table
        v-loading="loading"
        :data="configList"
        style="width: 100%"
        border
        stripe
        :max-height="windowHeight - 220"
        class="config-table"
        highlight-current-row
      >
        <el-table-column
          prop="key"
          label="配置键"
          min-width="280"
          fixed="left"
          show-overflow-tooltip
        />

        <el-table-column prop="value" label="配置值" min-width="350" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="editableIndex === configList.indexOf(row)" class="edit-cell">
              <el-input
                v-model="editForm.value"
                :placeholder="row.value"
                @keyup.enter="handleSaveEdit(row)"
              />
            </div>
            <span v-else class="value-cell">{{ row.value }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="350" show-overflow-tooltip>
          <template #default="{ row }">
            <div v-if="editableIndex === configList.indexOf(row)" class="edit-cell">
              <el-input
                v-model="editForm.description"
                :placeholder="row.description || '请输入描述'"
                @keyup.enter="handleSaveEdit(row)"
              />
            </div>
            <span v-else>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="updated_at"
          label="更新时间"
          min-width="180"
          align="center"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" min-width="180" align="center" fixed="right">
          <template #default="{ row, $index }">
            <div v-if="editableIndex === $index" class="edit-actions">
              <el-button type="primary" :icon="Check" @click="handleSaveEdit(row)">
                保存
              </el-button>

              <el-button type="info" :icon="Close" @click="cancelEdit"> 取消 </el-button>
            </div>
            <div v-else class="normal-actions">
              <el-button type="primary" :icon="Edit" @click="handleEdit(row, $index)">
                编辑
              </el-button>

              <el-button type="danger" :icon="Delete" @click="handleDelete(row)"> 删除 </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增配置对话框 -->
    <el-dialog v-model="createDialogVisible" title="新增配置" width="500px">
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="配置键" prop="config_key">
          <el-input
            v-model="createForm.config_key"
            placeholder="请输入配置键名称，如：APP_NAME"
          />
        </el-form-item>
        <el-form-item label="配置值" prop="value">
          <el-input
            v-model="createForm.value"
            placeholder="请输入配置值"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            placeholder="请输入配置描述"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateConfig" :loading="createLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Edit,
  Delete,
  Check,
  Close,
  Plus
} from '@element-plus/icons-vue'
import { getConfigs, updateConfig, deleteConfig, createConfig } from '@/api/config'
import type { SystemConfig } from '@/api/config'
import type { FormInstance, FormRules } from 'element-plus'

// 加载状态
const loading = ref(false)

// 配置列表
const configList = ref<SystemConfig[]>([])

// 搜索条件
const searchPrefix = ref('')

// 编辑相关
const editableIndex = ref(-1)
const editForm = reactive({
  key: '',
  value: '',
  description: '',
})

// 新增配置相关
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  config_key: '',
  value: '',
  description: '',
})

// 新增配置验证规则
const createRules = reactive<FormRules>({
  config_key: [
    { required: true, message: '请输入配置键', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '配置键应为大写字母、数字和下划线组成', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在2到50个字符', trigger: 'blur' }
  ],
  value: [
    { required: true, message: '请输入配置值', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入配置描述', trigger: 'blur' }
  ]
})

// 监听窗口高度变化，用于自适应表格高度
const windowHeight = ref(window.innerHeight)
const handleResize = () => {
  windowHeight.value = window.innerHeight
}

// 获取配置列表
const fetchConfigs = async () => {
  try {
    loading.value = true

    const params: { prefix?: string } = {}
    if (searchPrefix.value) {
      params.prefix = searchPrefix.value
    }

    const res = await getConfigs(params)

    // 转换对象为数组
    if (typeof res === 'object' && res !== null) {
      const configs: SystemConfig[] = []
      for (const key in res) {
        if (Object.prototype.hasOwnProperty.call(res, key)) {
          configs.push({
            key,
            value: res[key].value || '',
            description: res[key].description || '',
            updated_at: '',
          })
        }
      }
      configList.value = configs
    } else {
      configList.value = []
    }
  } catch (error) {
    console.error('获取配置列表失败:', error)
    ElMessage.error('获取配置列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  fetchConfigs()
}

// 重置查询
const resetQuery = () => {
  searchPrefix.value = ''
  fetchConfigs()
}

// 编辑配置
const handleEdit = (row: SystemConfig, index: number) => {
  editableIndex.value = index
  editForm.key = row.key
  editForm.value = row.value
  editForm.description = row.description || ''
}

// 取消编辑
const cancelEdit = () => {
  editableIndex.value = -1
  editForm.key = ''
  editForm.value = ''
  editForm.description = ''
}

// 保存编辑
const handleSaveEdit = async (row: SystemConfig) => {
  try {
    if (editForm.value === row.value && editForm.description === row.description) {
      // 如果没有修改，直接取消编辑
      cancelEdit()
      return
    }

    // 更新配置
    await updateConfig(row.key, {
      value: editForm.value,
      description: editForm.description,
    })

    // 更新本地数据
    row.value = editForm.value
    row.description = editForm.description

    ElMessage.success('更新配置成功')
    cancelEdit()
  } catch (error) {
    console.error('更新配置失败:', error)
    ElMessage.error('更新配置失败')
  }
}

// 删除配置
const handleDelete = (row: SystemConfig) => {
  ElMessageBox.confirm(`确定要删除配置 "${row.key}" 吗？`, '删除配置', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await deleteConfig(row.key)
        // 更新列表
        configList.value = configList.value.filter((item) => item.key !== row.key)
        ElMessage.success('删除成功')
      } catch (error) {
        console.error('删除配置失败:', error)
        ElMessage.error('删除配置失败')
      }
    })
    .catch(() => {})
}

// 打开创建配置对话框
const openCreateDialog = () => {
  createDialogVisible.value = true
  // 重置表单
  createForm.config_key = ''
  createForm.value = ''
  createForm.description = ''
  // 重置表单验证
  if (createFormRef.value) {
    createFormRef.value.resetFields()
  }
}

// 创建新配置
const handleCreateConfig = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      createLoading.value = true

      // 调用API创建配置
      await createConfig({
        config_key: createForm.config_key,
        value: createForm.value,
        description: createForm.description
      })

      // 关闭对话框
      createDialogVisible.value = false

      // 提示成功
      ElMessage.success('创建配置成功')

      // 刷新列表
      fetchConfigs()
    } catch (error) {
      console.error('创建配置失败:', error)
      ElMessage.error('创建配置失败')
    } finally {
      createLoading.value = false
    }
  })
}

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'

  const date = new Date(dateString)

  // 处理无效日期
  if (isNaN(date.getTime())) return '-'

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

// 页面加载时获取配置列表
onMounted(() => {
  fetchConfigs()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.config-container {
  width: 100%;

  .config-card {
    margin: 0;
    width: 100%;

    :deep(.el-card__body) {
      padding: 20px;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-title {
      font-weight: bold;
    }
  }

  .config-table {
    width: 100%;

    :deep(.el-table__header th) {
      font-weight: bold;
      background-color: #f5f7fa;
      color: #333;
      padding: 12px 0;
    }

    :deep(.el-table__row) {
      line-height: 1.6;
    }

    :deep(.el-table__cell) {
      padding: 12px 0;
    }

    .value-cell {
      font-family: Consolas, monospace;
      word-break: break-all;
    }
  }

  .edit-cell {
    margin: 5px 0;
    width: 100%;
  }

  .edit-actions,
  .normal-actions {
    display: flex;
    justify-content: center;
    gap: 15px;
  }
}

/* 宽屏适配 */
@media (min-width: 1600px) {
  .config-container {
    .config-table {
      :deep(.el-table__row) {
      }

      :deep(.el-table__header th) {
      }
    }
  }
}

@media (min-width: 2000px) {
  .config-container {
    max-width: 95%;
    margin: 0 auto;

    .card-header .header-title {
    }

    .config-table {
      :deep(.el-table__row) {
      }
    }
  }
}
</style>
