<template>
  <div class="style-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>风格管理</span>
          <el-button type="primary" @click="handleAddStyle">新增风格</el-button>
        </div>
      </template>

      <!-- 搜索和筛选区域 -->
      <div class="filter-container">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入风格名称"
          style="width: 200px;"
          class="filter-item"
          @keyup.enter="handleSearch"
        />

        <el-select
          v-model="queryParams.category"
          placeholder="风格分类"
          clearable
          style="width: 130px"
          class="filter-item"
        >
          <el-option
            v-for="item in categoryOptionsForFilter"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <el-select
          v-model="queryParams.is_active"
          placeholder="状态"
          clearable
          style="width: 130px"
          class="filter-item"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
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

      <!-- 风格表格 -->
      <el-table
        v-loading="loading"
        :data="styleList"
        style="width: 100%;"
        border
        row-key="id"
        :default-sort="{ prop: 'sort_order', order: 'ascending' }"
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
          prop="preview_url"
          label="预览图"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-image
              style="width: 60px; height: 60px;"
              :src="row.preview_url"
              fit="cover"
              :preview-src-list="[row.preview_url]"
            />
          </template>
        </el-table-column>

        <el-table-column
          prop="reference_image_url"
          label="参考图"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-image
              v-if="row.reference_image_url"
              style="width: 60px; height: 60px;"
              :src="row.reference_image_url"
              fit="cover"
              :preview-src-list="[row.reference_image_url]"
            />
            <span v-else>无</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="name"
          label="风格名称"
          min-width="120"
        />

        <el-table-column
          prop="category_info.name"
          label="分类"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :color="row.category_info?.color" effect="dark" v-if="row.category_info">{{ row.category_info.name }}</el-tag>
            <span v-else>未分类</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="credits_cost"
          label="所需积分"
          width="100"
          align="center"
        />

        <el-table-column
          prop="is_active"
          label="状态"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleStatusChange(row)"
              active-color="#13ce66"
              inactive-color="#ff4949"
            />
          </template>
        </el-table-column>

        <el-table-column
          prop="sort_order"
          label="排序"
          width="120"
          align="center"
          sortable
        >
          <template #default="{ row }">
            <div class="sort-control">
              <span>{{ row.sort_order }}</span>
              <div class="sort-buttons">
                <el-button
                  type="primary"
                  :icon="ArrowUp"
                  circle
                  size="small"
                  @click="handleSortChange(row, 'up')"
                />
                <el-button
                  type="primary"
                  :icon="ArrowDown"
                  circle
                  size="small"
                  @click="handleSortChange(row, 'down')"
                />
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          prop="prompt"
          label="AI提示词"
          min-width="120"
        >
          <template #default="{ row }">
            <el-tooltip
              class="box-item"
              effect="dark"
              :content="row.prompt"
              placement="top-start"
            >
              <span>{{ row.prompt && row.prompt.length > 20 ? row.prompt.substring(0, 20) + '...' : row.prompt }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column
          prop="created_at"
          label="创建时间"
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
          label="操作"
          fixed="right"
          width="180"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="Edit"
              @click="handleEditStyle(row)"
            >
              编辑
            </el-button>

            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="handleDeleteStyle(row)"
            >
              删除
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

    <!-- 添加/编辑风格对话框 -->
    <el-dialog
      v-model="styleDialogVisible"
      :title="dialogType === 'add' ? '新增风格' : '编辑风格'"
      width="600px"
    >
      <el-form
        ref="styleFormRef"
        :model="styleForm"
        :rules="styleRules"
        label-width="100px"
      >
        <el-form-item label="风格名称" prop="name">
          <el-input v-model="styleForm.name" placeholder="请输入风格名称" />
        </el-form-item>

        <el-form-item label="预览图" prop="preview_url">
          <el-upload
            class="style-image-uploader"
            action="#"
            :http-request="uploadImage"
            :show-file-list="false"
            :before-upload="beforeImageUpload"
          >
            <el-image
              v-if="styleForm.preview_url"
              :src="styleForm.preview_url"
              class="style-image"
            />
            <el-icon v-else class="style-image-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="el-upload__tip">
            支持jpg、png、jpeg格式，不超过2MB
          </div>
        </el-form-item>

        <el-form-item label="参考图" prop="reference_image_url">
          <el-upload
            class="style-image-uploader"
            action="#"
            :http-request="uploadReferenceImage"
            :show-file-list="false"
            :before-upload="beforeImageUpload"
          >
            <el-image
              v-if="styleForm.reference_image_url"
              :src="styleForm.reference_image_url"
              class="style-image"
            />
            <el-icon v-else class="style-image-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="el-upload__tip">
            支持jpg、png、jpeg格式，不超过2MB（可选）
          </div>
        </el-form-item>

        <el-form-item label="分类" prop="category_id">
          <el-select
            v-model="styleForm.category_id"
            placeholder="请选择分类"
            style="width: 100%"
          >
            <el-option
              v-for="item in categoryList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="积分消耗" prop="credits_cost">
          <el-input-number
            v-model="styleForm.credits_cost"
            :min="0"
            :precision="0"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="排序" prop="sort_order">
          <el-input-number
            v-model="styleForm.sort_order"
            :min="0"
            :precision="0"
            style="width: 30%"
          />
        </el-form-item>

        <el-form-item label="AI提示词" prop="prompt">
          <el-input
            v-model="styleForm.prompt"
            type="textarea"
            :rows="3"
            placeholder="请输入AI生成时使用的提示词"
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="styleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入风格描述"
          />
        </el-form-item>

        <el-form-item label="状态" prop="is_active">
          <el-switch
            v-model="styleForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="styleDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="submitStyleForm">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Edit, Delete, ArrowUp, ArrowDown, Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadProps } from 'element-plus'
import { getStyles, createStyle, updateStyle, deleteStyle } from '@/api/style'
import { getCategories } from '@/api/category'
import { uploadFile } from '@/api/upload'
import type { Style } from '@/api/style'

// 加载状态
const loading = ref(false)
const submitLoading = ref(false)

// 风格列表数据
const styleList = ref<Style[]>([])
const total = ref(0)

// 分类选项
const categoryOptions = [
  { value: '艺术', label: '艺术' },
  { value: '写实', label: '写实' },
  { value: '卡通', label: '卡通' },
  { value: '素描', label: '素描' },
  { value: '水彩', label: '水彩' },
  { value: '油画', label: '油画' },
  { value: '其他', label: '其他' }
]

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  skip: 0,
  name: '',
  category: '',
  is_active: undefined as boolean | undefined
})

// 风格表单对话框
const styleDialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const styleFormRef = ref<FormInstance>()
const styleForm = reactive<Partial<Style>>({
  name: '',
  description: '',
  preview_url: '',
  reference_image_url: '',
  category_id: undefined,
  prompt: '',
  credits_cost: 10,
  is_active: true,
  sort_order: 0
})

// 表单验证规则
const styleRules: FormRules = {
  name: [
    { required: true, message: '请输入风格名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  preview_url: [
    { required: true, message: '请上传预览图', trigger: 'change' }
  ],
  category_id: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  credits_cost: [
    { required: true, message: '请输入积分消耗', trigger: 'blur' }
  ],
  prompt: [
    { required: true, message: '请输入AI提示词', trigger: 'blur' }
  ]
}

// 定义Category接口
interface Category {
  id: number
  name: string
  description?: string
  icon?: string
  color?: string
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 获取分类列表
const categoryList = ref<Category[]>([]);
const fetchCategoryList = async () => {
  try {
    const res = await getCategories({ page: 1, limit: 100, is_active: true });

    // 处理不同的返回数据格式
    if (Array.isArray(res)) {
      categoryList.value = res;
    } else if (res && typeof res === 'object' && 'data' in res) {
      categoryList.value = res.data || [];
    } else {
      categoryList.value = [];
    }
  } catch (error) {
    console.error('获取分类列表失败:', error);
    categoryList.value = [];
  }
};

// 获取风格列表
const getStyleList = async () => {
  try {
    loading.value = true
    queryParams.skip = (queryParams.page - 1) * queryParams.limit

    const res = await getStyles(queryParams)
    console.log('API返回数据:', res) // 添加调试日志

    // 直接处理数组形式的响应
    if (Array.isArray(res)) {
      styleList.value = res
      total.value = res.length
    }
    // 处理分页格式的响应 {items: [], total: 0}
    else if (res && typeof res === 'object' && 'items' in res && 'total' in res) {
      styleList.value = res.items || []
      total.value = res.total || 0
    }
    // 处理可能的其他格式响应
    else if (res && typeof res === 'object') {
      // 尝试将对象转为数组
      const items = Object.values(res).filter(item =>
        typeof item === 'object' && item !== null && 'id' in item
      ) as Style[]

      if (items.length > 0) {
        styleList.value = items
        total.value = items.length
      } else {
        styleList.value = []
        total.value = 0
      }
    } else {
      styleList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取风格列表失败:', error)
    styleList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 搜索按钮点击事件
const handleSearch = () => {
  queryParams.page = 1
  getStyleList()
}

// 重置查询条件
const resetQuery = () => {
  queryParams.name = ''
  queryParams.category = ''
  queryParams.is_active = undefined
  queryParams.page = 1
  getStyleList()
}

// 状态切换
const handleStatusChange = async (row: Style) => {
  try {
    await updateStyle(row.id, { is_active: row.is_active })
    ElMessage.success(`已${row.is_active ? '启用' : '禁用'}该风格`)
  } catch (error) {
    console.error('更新风格状态失败:', error)
    // 恢复原始状态
    row.is_active = !row.is_active
  }
}

// 排序调整
const handleSortChange = async (row: Style, direction: 'up' | 'down') => {
  const newSortOrder = direction === 'up' ? row.sort_order - 1 : row.sort_order + 1

  // 确保排序值不小于0
  if (newSortOrder < 0) {
    ElMessage.warning('已经是最顶部了')
    return
  }

  try {
    await updateStyle(row.id, { sort_order: newSortOrder })
    // 更新本地数据
    row.sort_order = newSortOrder
    // 重新排序列表
    styleList.value.sort((a, b) => a.sort_order - b.sort_order)
    ElMessage.success('排序更新成功')
  } catch (error) {
    console.error('更新排序失败:', error)
  }
}

// 处理添加风格
const handleAddStyle = () => {
  resetStyleForm()
  dialogType.value = 'add'
  styleDialogVisible.value = true
}

// 处理编辑风格
const handleEditStyle = (row: Style) => {
  resetStyleForm()
  dialogType.value = 'edit'
  // 填充表单数据
  Object.assign(styleForm, row)
  styleDialogVisible.value = true
}

// 处理删除风格
const handleDeleteStyle = (row: Style) => {
  ElMessageBox.confirm(
    `确定要删除风格 "${row.name}" 吗？该操作不可逆，如果该风格已被作品使用，将无法删除。`,
    '删除风格',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteStyle(row.id)
      ElMessage.success('删除成功')
      getStyleList() // 重新获取列表
    } catch (error: any) {
      if (error.response && error.response.status === 409) {
        ElMessage.error('该风格已被作品使用，无法删除')
      } else {
        console.error('删除风格失败:', error)
        ElMessage.error('删除失败，请稍后重试')
      }
    }
  }).catch(() => {})
}

// 重置风格表单
const resetStyleForm = () => {
  styleForm.id = undefined
  styleForm.name = ''
  styleForm.description = ''
  styleForm.preview_url = ''
  styleForm.reference_image_url = ''
  styleForm.category_id = undefined
  styleForm.prompt = ''
  styleForm.credits_cost = 10
  styleForm.is_active = true
  styleForm.sort_order = 0
}

// 图片上传前验证
const beforeImageUpload: UploadProps['beforeUpload'] = (file) => {
  // 检查类型
  const isValidType = ['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)
  // 检查大小，限制为2MB
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isValidType) {
    ElMessage.error('图片只能是 JPG 或 PNG 格式!')
  }

  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
  }

  return isValidType && isLt2M
}

// 自定义上传
const uploadImage = async (options: any) => {
  const file = options.file
  try {
    // 调用上传API
    const response = await uploadFile(file, 'styles')
    if (response && response.url) {
      styleForm.preview_url = response.url
      ElMessage.success('预览图上传成功')
    } else {
      ElMessage.error('预览图上传失败：服务器未返回有效URL')
    }
  } catch (error) {
    console.error('上传预览图失败:', error)
    ElMessage.error('上传预览图失败')
  }
}

// 自定义上传参考图
const uploadReferenceImage = async (options: any) => {
  const file = options.file
  try {
    // 调用上传API
    const response = await uploadFile(file, 'styles')
    if (response && response.url) {
      styleForm.reference_image_url = response.url
      ElMessage.success('参考图上传成功')
    } else {
      ElMessage.error('参考图上传失败：服务器未返回有效URL')
    }
  } catch (error) {
    console.error('上传参考图失败:', error)
    ElMessage.error('上传参考图失败')
  }
}

// 提交表单
const submitStyleForm = () => {
  styleFormRef.value?.validate(async (valid) => {
    if (valid) {
      try {
        submitLoading.value = true

        if (dialogType.value === 'add') {
          // 新增风格
          await createStyle(styleForm as Omit<Style, 'id' | 'created_at'>)
          ElMessage.success('新增风格成功')
        } else {
          // 编辑风格
          if (!styleForm.id) return
          await updateStyle(styleForm.id, styleForm)
          ElMessage.success('编辑风格成功')
        }

        // 关闭对话框，刷新列表
        styleDialogVisible.value = false
        getStyleList()
      } catch (error) {
        console.error('提交风格表单失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 分页处理
const handleSizeChange = (size: number) => {
  queryParams.limit = size
  queryParams.page = 1
  getStyleList()
}

const handleCurrentChange = (page: number) => {
  queryParams.page = page
  getStyleList()
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

// 筛选区域的分类选项，可以从 categoryList 生成，或者保持手动定义
// 如果保持手动，需要确保 value 和后端接受的筛选值一致
// 如果从 API 获取，则使用 categoryList
const categoryOptionsForFilter = computed(() => {
  return categoryList.value.map(cat => ({ value: cat.name, label: cat.name })); // 假设筛选按名称进行
  // 或者 return categoryList.value.map(cat => ({ value: cat.id, label: cat.name })); // 假设筛选按 ID 进行
});

// 页面加载时获取风格列表
onMounted(() => {
  getStyleList()
  fetchCategoryList() // 加载分类数据
})
</script>

<style scoped lang="scss">
.style-container {
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

  .sort-control {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .sort-buttons {
      display: flex;
      flex-direction: column;
      gap: 5px;
      align-items: center;
    }
  }

  .style-image-uploader {
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;

    &:hover {
      border-color: #409eff;
    }

    .style-image {
      width: 150px;
      height: 150px;
      display: block;
      object-fit: cover;
    }

    .style-image-uploader-icon {
      font-size: 28px;
      color: #8c939d;
      width: 150px;
      height: 150px;
      display: flex;
      justify-content: center;
      align-items: center;
    }
  }
}
</style>
