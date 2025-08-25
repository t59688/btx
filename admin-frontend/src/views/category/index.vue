<template>
  <div class="category-container">
    <div class="filter-container">
      <el-form :inline="true" :model="filterForm" class="filter-form" @submit.prevent>
        <el-form-item label="分类名称">
          <el-input v-model="filterForm.name" placeholder="请输入分类名称" clearable @keyup.enter="handleFilter" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.is_active" placeholder="请选择状态" clearable @change="handleFilter" style="width: 120px">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="action-container">
      <el-button type="primary" @click="handleCreate">
        创建分类
      </el-button>
    </div>

    <el-table
      v-loading="tableLoading"
      :data="tableData"
      border
      fit
      highlight-current-row
      style="width: 100%"
    >
      <el-table-column prop="id" label="ID" align="center" width="80" />
      <el-table-column prop="name" label="分类名称" min-width="120" />
      <el-table-column label="图标" align="center" width="100">
        <template #default="{ row }">
          <el-popover
            placement="right"
            trigger="hover"
            width="200"
            v-if="row.icon"
          >
            <template #default>
              <div class="popover-image-container">
                <img :src="row.icon" class="popover-image" />
              </div>
            </template>
            <template #reference>
              <el-image
                :src="row.icon"
                style="width: 40px; height: 40px;"
                fit="cover"
                :preview-src-list="[row.icon]"
              />
            </template>
          </el-popover>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
      <el-table-column label="颜色" align="center" width="100">
        <template #default="{ row }">
          <div class="color-box" :style="{ backgroundColor: row.color || '#c0c4cc' }" />
          <span class="color-text">{{ row.color || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序值" align="center" width="100" />
      <el-table-column prop="created_at" label="创建时间" align="center" width="180" />
      <el-table-column prop="updated_at" label="更新时间" align="center" width="180" />
      <el-table-column label="操作" align="center" width="200">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button
            type="danger"
            size="small"
            @click="handleDelete(row)"
            :disabled="hasStyles(row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑分类的对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '创建分类' : '编辑分类'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        @submit.prevent
      >
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-upload
            class="avatar-uploader"
            action="#"
            :show-file-list="false"
            :http-request="uploadIcon"
            :before-upload="beforeIconUpload"
          >
            <img v-if="form.icon" :src="form.icon" class="avatar" />
            <div v-else class="avatar-uploader-icon">
              <el-icon><Plus /></el-icon>
            </div>
          </el-upload>
          <div class="upload-tip">点击上传图标，建议尺寸：64x64px，格式：PNG、JPG</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-color-picker v-model="form.color" show-alpha />
          <el-input v-model="form.color" placeholder="#RRGGBB" class="color-input" />
        </el-form-item>
        <el-form-item label="排序值" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item v-if="dialogType === 'edit'" label="状态" prop="is_active">
          <el-switch
            v-model="form.is_active"
            :active-value="true"
            :inactive-value="false"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { getCategories, createCategory, updateCategory, deleteCategory } from '@/api/category'
import { uploadFile } from '@/api/upload'
import { Plus } from '@element-plus/icons-vue'

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
  styles_count?: number
}

// 表格数据
const tableData = ref<Category[]>([])
const tableLoading = ref<boolean>(false)
const total = ref<number>(0)
const currentPage = ref<number>(1)
const pageSize = ref<number>(10)

// 筛选表单
const filterForm = reactive({
  name: '',
  is_active: undefined as boolean | undefined
})

// 创建/编辑表单
const formRef = ref<FormInstance>()
const form = reactive({
  id: 0,
  name: '',
  description: '',
  color: '',
  icon: '',
  sort_order: 0,
  is_active: true
})

// 表单校验规则
const formRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  color: [
    { pattern: /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$/, message: '请输入有效的颜色值', trigger: 'blur' }
  ],
  sort_order: [
    { required: true, message: '请输入排序值', trigger: 'blur' }
  ]
}

// 对话框控制
const dialogVisible = ref<boolean>(false)
const dialogType = ref<'create' | 'edit'>('create')

// 页面加载时获取数据
onMounted(() => {
  fetchData()
})

// 获取分类数据
const fetchData = async () => {
  tableLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      name: filterForm.name || undefined,
      is_active: filterForm.is_active
    }

    const res = await getCategories(params)
    console.log('API返回数据:', res)

    // 检查返回数据是否为数组
    if (Array.isArray(res)) {
      tableData.value = res
      total.value = res.length
    }
    // 检查返回数据是否为包含data和total属性的对象
    else if (res && typeof res === 'object' && 'data' in res) {
      tableData.value = res.data || []
      total.value = res.total || res.data.length || 0
    }
    // 其他情况
    else {
      tableData.value = []
      total.value = 0
      console.error('未识别的API返回格式:', res)
    }
  } catch (error) {
    console.error('获取分类列表失败:', error)
    ElMessage.error('获取分类列表失败')
    tableData.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

// 检查分类是否有关联的风格
const hasStyles = (row: Category): boolean => {
  return (row.styles_count || 0) > 0
}

// 处理筛选
const handleFilter = () => {
  currentPage.value = 1
  fetchData()
}

// 重置筛选
const resetFilter = () => {
  filterForm.name = ''
  filterForm.is_active = undefined
  currentPage.value = 1
  fetchData()
}

// 处理页码改变
const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchData()
}

// 处理每页数量改变
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
  fetchData()
}

// 处理创建分类
const handleCreate = () => {
  resetForm()
  dialogType.value = 'create'
  dialogVisible.value = true
}

// 处理编辑分类
const handleEdit = (row: Category) => {
  resetForm()
  dialogType.value = 'edit'
  Object.assign(form, {
    id: row.id,
    name: row.name,
    description: row.description || '',
    color: row.color || '',
    icon: row.icon || '',
    sort_order: row.sort_order,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

// 处理删除分类
const handleDelete = (row: Category) => {
  if (hasStyles(row)) {
    ElMessage.warning('该分类下存在风格，无法删除')
    return
  }

  ElMessageBox.confirm(
    '确定要删除此分类吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteCategory(row.id)
      ElMessage.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('删除分类失败:', error)
      ElMessage.error('删除分类失败')
    }
  }).catch(() => {
    // 取消删除操作
  })
}

// 重置表单
const resetForm = () => {
  form.id = 0
  form.name = ''
  form.description = ''
  form.color = ''
  form.icon = ''
  form.sort_order = 0
  form.is_active = true

  // 重置表单校验
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (dialogType.value === 'create') {
        await createCategory({
          name: form.name,
          description: form.description,
          color: form.color,
          icon: form.icon,
          sort_order: form.sort_order
        })
        ElMessage.success('创建成功')
      } else {
        await updateCategory(form.id, {
          name: form.name,
          description: form.description,
          color: form.color,
          icon: form.icon,
          sort_order: form.sort_order,
          is_active: form.is_active
        })
        ElMessage.success('更新成功')
      }

      dialogVisible.value = false
      fetchData()
    } catch (error) {
      console.error(dialogType.value === 'create' ? '创建分类失败:' : '更新分类失败:', error)
      ElMessage.error(dialogType.value === 'create' ? '创建分类失败' : '更新分类失败')
    }
  })
}

// 处理图标上传
const uploadIcon = async (options: any) => {
  try {
    console.log('开始上传图标文件:', options.file)
    const file = options.file

    const response = await uploadFile(file, 'category_icons')
    console.log('上传图标响应:', response)

    if (response && response.url) {
      form.icon = response.url
      ElMessage.success('图标上传成功')
    } else {
      ElMessage.error('图标上传失败：服务器未返回有效URL')
    }
  } catch (error) {
    console.error('上传图标失败:', error)
    ElMessage.error('上传图标失败：' + (error instanceof Error ? error.message : String(error)))
  }
}

// 处理图标上传前的验证
const beforeIconUpload = (file: File) => {
  // 检查文件类型
  const isImage = file.type.startsWith('image/')

  // 检查文件大小（限制为2MB）
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }

  if (!isLt2M) {
    ElMessage.error('图片大小不能超过2MB!')
    return false
  }

  return true
}
</script>

<style scoped>
.category-container {
  padding: 20px;
}

.filter-container {
  margin-bottom: 20px;
}

.action-container {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.color-box {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  margin-right: 6px;
  vertical-align: middle;
  border: 1px solid #dcdfe6;
}

.color-text {
  vertical-align: middle;
  font-size: 12px;
}

.color-input {
  width: 120px;
  margin-left: 10px;
}

.preview-container {
  margin-top: 5px;
  display: flex;
  align-items: center;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-select-dropdown) {
  min-width: 120px !important;
}

.avatar-uploader {
  width: 120px;
  height: 120px;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-uploader:hover {
  border-color: #409eff;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.avatar {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.upload-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.popover-image-container {
  width: 200px;
  height: 200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.popover-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
</style>
