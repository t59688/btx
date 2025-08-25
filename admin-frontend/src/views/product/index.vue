<template>
  <div class="product-container">
    <el-card class="filter-container">
      <div class="filter-item">
        <el-input
          v-model="queryParams.search"
          placeholder="请输入商品名称"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="filter-item">
        <el-select v-model="queryParams.is_active" placeholder="上架状态" clearable>
          <el-option label="已上架" :value="true" />
          <el-option label="已下架" :value="false" />
        </el-select>
      </div>
      <div class="filter-item">
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button @click="resetQuery">
          <el-icon><Refresh /></el-icon>重置
        </el-button>
      </div>
    </el-card>

    <el-card class="table-container">
      <template #header>
        <div class="card-header">
          <span>商品列表</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>新增商品
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="productList"
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="商品图片" width="120">
          <template #default="scope">
            <el-image
              :src="scope.row.image_url"
              fit="cover"
              :preview-src-list="[scope.row.image_url]"
              class="product-image"
            />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="商品名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="商品描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="credits" label="积分" width="100" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            {{ scope.row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="上架状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'info'">
              {{ scope.row.is_active ? '已上架' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              link
              :type="scope.row.is_active ? 'warning' : 'success'"
              size="small"
              @click="handleToggleStatus(scope.row)"
            >
              {{ scope.row.is_active ? '下架' : '上架' }}
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- 添加/编辑商品对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="600px"
      append-to-body
    >
      <el-form
        ref="productFormRef"
        :model="productForm"
        :rules="productRules"
        label-width="100px"
      >
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="productForm.name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="商品描述" prop="description">
          <el-input
            v-model="productForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入商品描述"
          />
        </el-form-item>
        <el-form-item label="积分" prop="credits">
          <el-input-number
            v-model="productForm.credits"
            :min="1"
            placeholder="请输入积分"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number
            v-model="productForm.price"
            :min="0"
            :precision="2"
            :step="0.1"
            placeholder="请输入价格"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="商品图片" prop="image_url">
          <el-upload
            action="/upload"
            :headers="{ Authorization: 'Bearer ' + token }"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            :before-upload="beforeUpload"
            class="upload-container"
          >
            <img v-if="productForm.image_url" :src="productForm.image_url" class="upload-image" />
            <el-icon v-else class="upload-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">建议上传宽高比1:1的图片，大小不超过2MB</div>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number
            v-model="productForm.sort_order"
            :min="0"
            placeholder="请输入排序值（值越小排越前）"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="上架状态" prop="is_active">
          <el-switch v-model="productForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'
import { getProducts, createProduct, updateProduct, deleteProduct } from '@/api/product'
import type { Product, CreateProductRequest, UpdateProductRequest } from '@/types/product'
import { formatDateTime } from '@/utils/format'

// 获取token
const token = localStorage.getItem('token')

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  search: '',
  is_active: undefined
})

// 商品列表数据
const productList = ref<Product[]>([])
const loading = ref(false)
const total = ref(0)

// 表单相关
const dialogVisible = ref(false)
const dialogTitle = ref('')
const productFormRef = ref<FormInstance>()
const productForm = reactive<CreateProductRequest & {id?: number}>({
  name: '',
  description: '',
  credits: 0,
  price: 0,
  image_url: '',
  is_active: true,
  sort_order: 0
})

// 表单校验规则
const productRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入商品描述', trigger: 'blur' }],
  credits: [{ required: true, message: '请输入积分', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  image_url: [{ required: false, message: '请上传商品图片', trigger: 'change' }]
}

// 加载商品列表数据
const loadProducts = async () => {
  loading.value = true
  try {
    const res = await getProducts(queryParams)
    productList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取商品列表失败', error)
    ElMessage.error('获取商品列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  queryParams.page = 1
  loadProducts()
}

// 重置查询
const resetQuery = () => {
  queryParams.search = ''
  queryParams.is_active = undefined
  queryParams.page = 1
  loadProducts()
}

// 处理分页变化
const handleSizeChange = (size: number) => {
  queryParams.limit = size
  loadProducts()
}

const handleCurrentChange = (page: number) => {
  queryParams.page = page
  loadProducts()
}

// 新增商品
const handleAdd = () => {
  resetForm()
  dialogTitle.value = '新增商品'
  dialogVisible.value = true
}

// 编辑商品
const handleEdit = (row: Product) => {
  resetForm()
  dialogTitle.value = '编辑商品'
  // 复制行数据到表单
  Object.assign(productForm, row)
  dialogVisible.value = true
}

// 切换商品状态
const handleToggleStatus = async (row: Product) => {
  try {
    await updateProduct(row.id, { is_active: !row.is_active })
    ElMessage.success(`商品已${row.is_active ? '下架' : '上架'}`)
    loadProducts()
  } catch (error) {
    console.error('更新商品状态失败', error)
    ElMessage.error('操作失败')
  }
}

// 删除商品
const handleDelete = (row: Product) => {
  ElMessageBox.confirm(`确认要删除商品【${row.name}】吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteProduct(row.id)
      ElMessage.success('删除成功')
      loadProducts()
    } catch (error) {
      console.error('删除商品失败', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 重置表单
const resetForm = () => {
  productForm.id = undefined
  productForm.name = ''
  productForm.description = ''
  productForm.credits = 0
  productForm.price = 0
  productForm.image_url = ''
  productForm.is_active = true
  productForm.sort_order = 0
}

// 提交表单
const submitForm = async () => {
  if (!productFormRef.value) return

  await productFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (productForm.id) {
          // 编辑
          const updateData: UpdateProductRequest = { ...productForm }
          delete updateData.id
          await updateProduct(productForm.id, updateData)
          ElMessage.success('编辑成功')
        } else {
          // 新增
          await createProduct(productForm)
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
        loadProducts()
      } catch (error) {
        console.error('提交表单失败', error)
        ElMessage.error('操作失败')
      }
    }
  })
}

// 图片上传相关
const handleUploadSuccess = (res: any) => {
  productForm.image_url = res.url
}

const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('上传图片只能是图片格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('上传图片大小不能超过 2MB!')
    return false
  }
  return true
}

// 加载初始数据
onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.product-container {
  padding-bottom: 20px;
}

.filter-container {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 18px 20px;
}

.filter-item {
  margin-right: 10px;
  min-width: 200px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-image {
  width: 60px;
  height: 60px;
  border-radius: 4px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.upload-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 120px;
  height: 120px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.upload-container:hover {
  border-color: #409EFF;
}

.upload-icon {
  font-size: 28px;
  color: #8c939d;
}

.upload-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}
</style>
