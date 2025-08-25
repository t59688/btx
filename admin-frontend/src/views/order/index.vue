<template>
  <div class="order-container">
    <el-card class="filter-container">
      <div class="filter-item">
        <el-input
          v-model="queryParams.order_no"
          placeholder="请输入订单号"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="filter-item">
        <el-select v-model="queryParams.status" placeholder="订单状态" clearable>
          <el-option label="待支付" value="pending" />
          <el-option label="已支付" value="paid" />
          <el-option label="已完成" value="completed" />
          <el-option label="已取消" value="cancelled" />
          <el-option label="已退款" value="refunded" />
        </el-select>
      </div>
      <div class="filter-item date-range">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          :shortcuts="dateShortcuts"
        />
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
          <span>订单列表</span>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="orderList"
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="order_no" label="订单号" width="180" show-overflow-tooltip />
        <el-table-column label="用户信息" min-width="160">
          <template #default="scope">
            <div class="user-info">
              <el-avatar
                :size="32"
                :src="scope.row.user_avatar"
                class="user-avatar"
              ></el-avatar>
              <span>{{ scope.row.user_nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="商品信息" min-width="200">
          <template #default="scope">
            <div class="product-info">
              <div class="product-name">{{ scope.row.product_name }}</div>
              <div class="product-desc">{{ scope.row.product_description || '积分套餐' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="scope">
            {{ formatCurrency(scope.row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="credits" label="积分" width="100" />
        <el-table-column label="订单状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="180">
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
              @click="handleDetail(scope.row)"
            >
              详情
            </el-button>
            <el-button
              v-if="scope.row.status === 'paid'"
              link
              type="success"
              size="small"
              @click="handleComplete(scope.row)"
            >
              标记完成
            </el-button>
            <el-button
              v-if="['paid', 'completed'].includes(scope.row.status)"
              link
              type="warning"
              size="small"
              @click="handleRefund(scope.row)"
            >
              退款
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

    <!-- 订单详情对话框 -->
    <el-dialog
      title="订单详情"
      v-model="detailDialogVisible"
      width="700px"
      append-to-body
    >
      <div v-if="currentOrder" class="order-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">{{ currentOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ currentOrder.user_id }}</el-descriptions-item>
          <el-descriptions-item label="用户昵称">{{ currentOrder.user_nickname }}</el-descriptions-item>
          <el-descriptions-item label="商品名称">{{ currentOrder.product_name }}</el-descriptions-item>
          <el-descriptions-item label="商品描述">{{ currentOrder.product_description }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ formatCurrency(currentOrder.amount) }}</el-descriptions-item>
          <el-descriptions-item label="积分">{{ currentOrder.credits }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="getStatusType(currentOrder.status)">
              {{ getStatusText(currentOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentOrder.payment_id" label="支付流水号">
            {{ currentOrder.payment_id }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentOrder.payment_time" label="支付时间">
            {{ formatDateTime(currentOrder.payment_time) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentOrder.refund_time" label="退款时间">
            {{ formatDateTime(currentOrder.refund_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(currentOrder.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(currentOrder.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ currentOrder.remark || '无' }}</el-descriptions-item>
        </el-descriptions>

        <div class="order-actions">
          <el-form v-if="['pending', 'paid'].includes(currentOrder.status)" ref="remarkFormRef" :model="remarkForm">
            <el-form-item label="添加备注" prop="remark">
              <el-input
                v-model="remarkForm.remark"
                type="textarea"
                :rows="3"
                placeholder="请输入备注信息（可选）"
              />
            </el-form-item>
          </el-form>

          <div class="action-buttons">
            <el-button @click="detailDialogVisible = false">关闭</el-button>
            <el-button
              v-if="currentOrder.status === 'paid'"
              type="success"
              @click="handleCompleteWithRemark"
            >
              标记完成
            </el-button>
            <el-button
              v-if="['paid', 'completed'].includes(currentOrder.status)"
              type="warning"
              @click="handleRefundWithRemark"
            >
              退款
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getOrders, getOrderDetail, updateOrder, deleteOrder, refundOrder } from '@/api/order'
import type { Order, OrderStatus } from '@/types/order'
import { formatDateTime, formatCurrency } from '@/utils/format'

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    }
  }
]

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  status: undefined as OrderStatus | undefined,
  order_no: '',
  date_start: undefined as string | undefined,
  date_end: undefined as string | undefined
})

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 监听日期范围变化，更新查询参数
watch(dateRange, (val) => {
  if (val) {
    queryParams.date_start = val[0]
    queryParams.date_end = val[1]
  } else {
    queryParams.date_start = undefined
    queryParams.date_end = undefined
  }
})

// 订单列表数据
const orderList = ref<Order[]>([])
const loading = ref(false)
const total = ref(0)
const currentOrder = ref<Order | null>(null)
const detailDialogVisible = ref(false)

// 备注表单
const remarkFormRef = ref<FormInstance>()
const remarkForm = reactive({
  remark: ''
})

// 订单状态映射
const getStatusText = (status: OrderStatus) => {
  const statusMap: Record<OrderStatus, string> = {
    pending: '待支付',
    paid: '已支付',
    completed: '已完成',
    cancelled: '已取消',
    refunded: '已退款'
  }
  return statusMap[status] || status
}

// 订单状态标签类型
const getStatusType = (status: OrderStatus) => {
  const typeMap: Record<OrderStatus, string> = {
    pending: 'info',
    paid: 'warning',
    completed: 'success',
    cancelled: 'danger',
    refunded: 'danger'
  }
  return typeMap[status] || 'info'
}

// 加载订单列表数据
const loadOrders = async () => {
  loading.value = true
  try {
    const res = await getOrders(queryParams)
    orderList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取订单列表失败', error)
    ElMessage.error('获取订单列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  queryParams.page = 1
  loadOrders()
}

// 重置查询
const resetQuery = () => {
  queryParams.status = undefined
  queryParams.order_no = ''
  dateRange.value = null
  queryParams.date_start = undefined
  queryParams.date_end = undefined
  queryParams.page = 1
  loadOrders()
}

// 处理分页变化
const handleSizeChange = (size: number) => {
  queryParams.limit = size
  loadOrders()
}

const handleCurrentChange = (page: number) => {
  queryParams.page = page
  loadOrders()
}

// 查看订单详情
const handleDetail = async (row: Order) => {
  try {
    const orderDetail = await getOrderDetail(row.id)
    currentOrder.value = orderDetail
    remarkForm.remark = orderDetail.remark || ''
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取订单详情失败', error)
    ElMessage.error('获取订单详情失败')
  }
}

// 标记订单完成
const handleComplete = (row: Order) => {
  ElMessageBox.confirm(`确认要将订单【${row.order_no}】标记为已完成吗？`, '操作确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await updateOrder(row.id, { status: 'completed' })
      ElMessage.success('操作成功')
      loadOrders()
    } catch (error) {
      console.error('更新订单状态失败', error)
      ElMessage.error('操作失败')
    }
  }).catch(() => {})
}

// 带备注标记完成
const handleCompleteWithRemark = async () => {
  if (!currentOrder.value) return

  try {
    await updateOrder(currentOrder.value.id, {
      status: 'completed',
      remark: remarkForm.remark
    })
    ElMessage.success('操作成功')
    detailDialogVisible.value = false
    loadOrders()
  } catch (error) {
    console.error('更新订单状态失败', error)
    ElMessage.error('操作失败')
  }
}

// 退款订单
const handleRefund = (row: Order) => {
  ElMessageBox.confirm(`确认要对订单【${row.order_no}】进行退款吗？此操作不可逆！`, '退款确认', {
    confirmButtonText: '确定退款',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await refundOrder(row.id)
      ElMessage.success('退款成功')
      loadOrders()
    } catch (error) {
      console.error('订单退款失败', error)
      ElMessage.error('退款失败')
    }
  }).catch(() => {})
}

// 带备注退款
const handleRefundWithRemark = async () => {
  if (!currentOrder.value) return

  ElMessageBox.confirm(`确认要对订单【${currentOrder.value.order_no}】进行退款吗？此操作不可逆！`, '退款确认', {
    confirmButtonText: '确定退款',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 先更新备注
      if (remarkForm.remark) {
        await updateOrder(currentOrder.value!.id, { remark: remarkForm.remark })
      }
      // 然后执行退款
      await refundOrder(currentOrder.value!.id)
      ElMessage.success('退款成功')
      detailDialogVisible.value = false
      loadOrders()
    } catch (error) {
      console.error('订单退款失败', error)
      ElMessage.error('退款失败')
    }
  }).catch(() => {})
}

// 删除订单
const handleDelete = (row: Order) => {
  ElMessageBox.confirm(`确认要删除订单【${row.order_no}】吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteOrder(row.id)
      ElMessage.success('删除成功')
      loadOrders()
    } catch (error) {
      console.error('删除订单失败', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 加载初始数据
onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.order-container {
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

.date-range {
  min-width: 400px;
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

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  margin-right: 5px;
}

.product-info {
  display: flex;
  flex-direction: column;
}

.product-name {
  font-weight: bold;
  margin-bottom: 5px;
}

.product-desc {
  color: #666;
  font-size: 12px;
}

.order-detail {
  padding: 10px;
}

.order-actions {
  margin-top: 20px;
}

.action-buttons {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>
