<template>
  <div class="card-key-container">
    <el-card class="filter-container">
      <div class="filter-form">
        <el-form :inline="true" :model="queryParams" class="demo-form-inline">
          <el-form-item label="状态">
            <el-select v-model="queryParams.status" placeholder="全部状态" clearable>
              <el-option label="未使用" value="unused" />
              <el-option label="已使用" value="used" />
              <el-option label="已失效" value="invalid" />
            </el-select>
          </el-form-item>
          <el-form-item label="批次号">
            <el-input v-model="queryParams.batch_no" placeholder="输入批次号" clearable />
          </el-form-item>
          <el-form-item label="创建时间">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD HH:mm:ss"
              :default-time="['00:00:00', '23:59:59']"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card class="list-container">
      <template #header>
        <div class="card-header">
          <span>卡密列表</span>
          <el-button type="primary" @click="handleCreate">创建卡密</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="cardKeyList" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="card_key" label="卡密" width="120" />
        <el-table-column prop="credits" label="积分面值" width="100" />
        <el-table-column prop="batch_no" label="批次号" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'unused'
                  ? 'success'
                  : row.status === 'used'
                  ? 'info'
                  : 'danger'
              "
            >
              {{
                row.status === 'unused'
                  ? '未使用'
                  : row.status === 'used'
                  ? '已使用'
                  : '已失效'
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="used_at" label="使用时间" width="180" />
        <el-table-column prop="used_by_nickname" label="使用用户" width="120" />
        <el-table-column prop="expired_at" label="过期时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'unused'"
              type="primary"
              size="small"
              @click="handleInvalidate(row)"
              >标记失效</el-button
            >
            <el-button
              v-if="row.status === 'unused'"
              type="danger"
              size="small"
              @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:currentPage="queryParams.page"
          v-model:page-size="queryParams.per_page"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建卡密对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建卡密" width="500px">
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="积分面值" prop="credits">
          <el-input-number v-model="createForm.credits" :min="1" />
        </el-form-item>
        <el-form-item label="创建数量" prop="count">
          <el-input-number v-model="createForm.count" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="批次号" prop="batch_no">
          <el-input v-model="createForm.batch_no" placeholder="选填，不填自动生成" />
        </el-form-item>
        <el-form-item label="过期时间" prop="expired_at">
          <el-date-picker
            v-model="createForm.expired_at"
            type="datetime"
            placeholder="选择过期时间（选填）"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="createForm.remark"
            type="textarea"
            placeholder="选填"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreate" :loading="submitting">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCardKeys,
  createCardKeys,
  updateCardKeyStatus,
  deleteCardKey,
  type CardKey,
  type CardKeyQueryParams,
  type CreateCardKeyParams
} from '@/api/card-key'

// 查询参数
const queryParams = reactive<CardKeyQueryParams>({
  page: 1,
  per_page: 10,
  status: undefined,
  batch_no: undefined,
  created_start: undefined,
  created_end: undefined
})

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 监听日期范围变化
watch(dateRange, (newVal) => {
  if (newVal) {
    queryParams.created_start = newVal[0]
    queryParams.created_end = newVal[1]
  } else {
    queryParams.created_start = undefined
    queryParams.created_end = undefined
  }
})

// 卡密列表数据
const cardKeyList = ref<CardKey[]>([])
const total = ref(0)
const loading = ref(false)

// 获取卡密列表数据
const getList = async () => {
  loading.value = true
  try {
    const res = await getCardKeys(queryParams)
    cardKeyList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取卡密列表失败', error)
    ElMessage.error('获取卡密列表失败')
  } finally {
    loading.value = false
  }
}

// 查询按钮
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  queryParams.status = undefined
  queryParams.batch_no = undefined
  dateRange.value = null
  queryParams.created_start = undefined
  queryParams.created_end = undefined
  queryParams.page = 1
  getList()
}

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.per_page = size
  getList()
}

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page
  getList()
}

// 创建卡密相关
const createDialogVisible = ref(false)
const submitting = ref(false)
const createFormRef = ref()
const createForm = reactive<CreateCardKeyParams>({
  credits: 100,
  count: 10,
  batch_no: undefined,
  expired_at: undefined,
  remark: undefined
})

// 创建表单校验规则
const createRules = {
  credits: [{ required: true, message: '请输入积分面值', trigger: 'blur' }],
  count: [
    { required: true, message: '请输入创建数量', trigger: 'change' }
  ]
}

// 打开创建对话框
const handleCreate = () => {
  createForm.credits = 100
  createForm.count = 10
  createForm.batch_no = undefined
  createForm.expired_at = undefined
  createForm.remark = undefined
  createDialogVisible.value = true
}

// 提交创建
const submitCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true

    try {
      const res = await createCardKeys(createForm)
      // 确保从res.data中获取count值
      const responseData = res.data
      const count = responseData?.count || createForm.count
      ElMessage.success(`成功创建${count}个卡密`)
      createDialogVisible.value = false
      getList()
    } catch (error) {
      console.error('创建卡密失败', error)
      ElMessage.error('创建卡密失败')
    } finally {
      submitting.value = false
    }
  })
}

// 标记失效
const handleInvalidate = (row: CardKey) => {
  ElMessageBox.confirm(`确定要将卡密 ${row.card_key} 标记为失效吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await updateCardKeyStatus(row.id, { status: 'invalid' })
        ElMessage.success('操作成功')
        getList()
      } catch (error) {
        console.error('更新卡密状态失败', error)
        ElMessage.error('更新卡密状态失败')
      }
    })
    .catch(() => {
      // 用户取消操作
    })
}

// 删除卡密
const handleDelete = (row: CardKey) => {
  ElMessageBox.confirm(`确定要删除卡密 ${row.card_key} 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await deleteCardKey(row.id)
        ElMessage.success('删除成功')
        getList()
      } catch (error) {
        console.error('删除卡密失败', error)
        ElMessage.error('删除卡密失败')
      }
    })
    .catch(() => {
      // 用户取消操作
    })
}

// 页面加载时获取数据
onMounted(() => {
  getList()
})
</script>

<style scoped>
.card-key-container {
  padding: 20px;
}

.filter-container {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
