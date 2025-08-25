<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="statistic-card">
          <div class="statistic-title">用户总数</div>
          <div class="statistic-value">{{ statistics.userCount }}</div>
          <div class="statistic-icon">
            <el-icon><User /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="statistic-card">
          <div class="statistic-title">作品总数</div>
          <div class="statistic-value">{{ statistics.artworkCount }}</div>
          <div class="statistic-icon">
            <el-icon><PictureRounded /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="statistic-card">
          <div class="statistic-title">商品总数</div>
          <div class="statistic-value">{{ statistics.productCount }}</div>
          <div class="statistic-icon product-icon">
            <el-icon><GoodsFilled /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="statistic-card">
          <div class="statistic-title">订单总数</div>
          <div class="statistic-value">{{ statistics.orderCount }}</div>
          <div class="statistic-icon order-icon">
            <el-icon><List /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>近7天用户增长</span>
            </div>
          </template>
          <div class="chart-container" ref="userChartRef"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>近7天订单统计</span>
            </div>
          </template>
          <div class="chart-container" ref="orderChartRef"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>最近订单</span>
              <el-button type="text" @click="goToOrders">查看更多</el-button>
            </div>
          </template>
          <div v-if="recentOrders.length === 0" class="empty-data">
            <el-empty description="暂无订单数据" />
          </div>
          <el-table v-else :data="recentOrders" style="width: 100%" stripe>
            <el-table-column prop="order_no" label="订单号" width="160" />
            <el-table-column prop="user_nickname" label="用户" width="120" />
            <el-table-column prop="product_name" label="商品" min-width="120" />
            <el-table-column prop="amount" label="金额" width="100">
              <template #default="scope">
                {{ formatCurrency(scope.row.amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getOrderStatusType(scope.row.status)">
                  {{ getOrderStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>畅销商品</span>
              <el-button type="text" @click="goToProducts">管理商品</el-button>
            </div>
          </template>
          <div v-if="hotProducts.length === 0" class="empty-data">
            <el-empty description="暂无商品销售数据" />
          </div>
          <el-table v-else :data="hotProducts" style="width: 100%" stripe>
            <el-table-column label="商品" min-width="200">
              <template #default="scope">
                <div class="product-info">
                  <el-image
                    :src="scope.row.image_url"
                    fit="cover"
                    class="product-image"
                  />
                  <div class="product-detail">
                    <div class="product-name">{{ scope.row.name }}</div>
                    <div class="product-desc">{{ scope.row.description }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="单价" width="100">
              <template #default="scope">
                {{ formatCurrency(scope.row.price) }}
              </template>
            </el-table-column>
            <el-table-column prop="sales" label="销量" width="100" />
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'info'">
                  {{ scope.row.is_active ? '已上架' : '已下架' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, PictureRounded, GoodsFilled, List } from '@element-plus/icons-vue'
import { getStatistics, getProductSalesStats } from '@/api/stats'
import { getOrders } from '@/api/order'
import { getProducts } from '@/api/product'
import { formatDateTime, formatCurrency } from '@/utils/format'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { OrderStatus } from '@/types/order'
import type { Product } from '@/types/product'
import type { Statistics } from '@/api/stats'
import type { PaginatedResponse } from '@/types/product'

// 注册ECharts组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  BarChart,
  LineChart,
  CanvasRenderer
])

const router = useRouter()

interface ProductSales {
  productId: number
  productName: string
  salesCount: number
  totalAmount: number
}

// 统计数据
const statistics = reactive({
  userCount: 0,
  artworkCount: 0,
  productCount: 0,
  orderCount: 0,
  userStats: {} as Record<string, number>,
  orderStats: {} as Record<string, number>,
  revenueStats: {} as Record<string, number>
})

// 近期订单和热门商品
const recentOrders = ref<any[]>([])
const hotProducts = ref<(Product & { sales: number })[]>([])

// 图表DOM引用
const userChartRef = ref()
const orderChartRef = ref()

// 图表实例
let userChart: echarts.ECharts | null = null
let orderChart: echarts.ECharts | null = null

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const response = await getStatistics()
    // 处理返回数据，解析出实际需要的数据结构
    const res = response && typeof response === 'object' && 'data' in response
      ? (response.data as Statistics)
      : (response as unknown as Statistics)

    statistics.userCount = res.userCount || 0
    statistics.artworkCount = res.artworkCount || 0
    statistics.productCount = res.productCount || 0
    statistics.orderCount = res.orderCount || 0
    statistics.userStats = res.userStats || {}
    statistics.orderStats = res.orderStats || {}
    statistics.revenueStats = res.revenueStats || {}

    // 初始化图表
    initUserChart()
    initOrderChart()
  } catch (error) {
    console.error('获取统计数据失败', error)
    ElMessage.error('获取统计数据失败')
  }
}

// 获取最近订单
const fetchRecentOrders = async () => {
  try {
    const response = await getOrders({
      page: 1,
      limit: 5
    })

    // 处理返回数据结构
    const res = response && typeof response === 'object' && 'data' in response
      ? (response.data as PaginatedResponse<any>)
      : (response as unknown as PaginatedResponse<any>)

    recentOrders.value = res.items || []
  } catch (error) {
    console.error('获取最近订单失败', error)
  }
}

// 获取热门商品
const fetchHotProducts = async () => {
  try {
    // 获取商品销售统计
    const salesResponse = await getProductSalesStats()

    // 处理返回数据结构
    const salesData = salesResponse && typeof salesResponse === 'object' && 'data' in salesResponse
      ? (salesResponse.data as ProductSales[])
      : (salesResponse as unknown as ProductSales[])

    if (!salesData || !Array.isArray(salesData) || salesData.length === 0) {
      return
    }

    // 按销量排序并只取前5个
    const topSales = salesData
      .sort((a, b) => b.salesCount - a.salesCount)
      .slice(0, 5)

    // 获取这些商品的详细信息
    const productsMap = new Map<number, Product>()

    // 获取所有需要的商品详情
    const productIds = topSales.map(item => item.productId)

    if (productIds.length > 0) {
      // 根据实际API结构调整，这里假设getProducts可以批量获取
      const productsResponse = await getProducts({
        page: 1,
        limit: productIds.length,
        is_active: true
      })

      // 处理返回数据结构
      const productsRes = productsResponse && typeof productsResponse === 'object' && 'data' in productsResponse
        ? (productsResponse.data as PaginatedResponse<Product>)
        : (productsResponse as unknown as PaginatedResponse<Product>)

      if (productsRes && Array.isArray(productsRes.items)) {
        for (const product of productsRes.items) {
          productsMap.set(product.id, product)
        }
      }
    }

    // 合并商品详情和销量数据
    hotProducts.value = topSales
      .filter(sale => productsMap.has(sale.productId))
      .map(sale => ({
        ...(productsMap.get(sale.productId) as Product),
        sales: sale.salesCount
      }))
  } catch (error) {
    console.error('获取热门商品失败', error)
  }
}

// 获取过去7天的日期数组
const getLast7Days = () => {
  const dates = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const formatDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    dates.push({
      full: formatDate,
      display: `${date.getMonth() + 1}/${date.getDate()}`
    })
  }
  return dates
}

// 初始化用户增长图表
const initUserChart = () => {
  if (!userChartRef.value) return

  // 销毁旧图表
  if (userChart) {
    userChart.dispose()
  }

  userChart = echarts.init(userChartRef.value)

  // 获取过去7天的日期
  const days = getLast7Days()
  const dates = days.map(day => day.display)

  // 使用真实数据
  const userData = days.map(day => statistics.userStats[day.full] || 0)

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '新增用户',
        type: 'line',
        data: userData,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#409EFF'
        },
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(64, 158, 255, 0.7)'
            },
            {
              offset: 1,
              color: 'rgba(64, 158, 255, 0.1)'
            }
          ])
        }
      }
    ]
  }

  userChart.setOption(option)
}

// 初始化订单统计图表
const initOrderChart = () => {
  if (!orderChartRef.value) return

  // 销毁旧图表
  if (orderChart) {
    orderChart.dispose()
  }

  orderChart = echarts.init(orderChartRef.value)

  // 获取过去7天的日期
  const days = getLast7Days()
  const dates = days.map(day => day.display)

  // 使用真实数据
  const orderData = days.map(day => statistics.orderStats[day.full] || 0)
  const amountData = days.map(day => statistics.revenueStats[day.full] || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['订单数', '交易额']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: '订单数',
        position: 'left'
      },
      {
        type: 'value',
        name: '交易额',
        position: 'right',
        axisLabel: {
          formatter: '{value} 元'
        }
      }
    ],
    series: [
      {
        name: '订单数',
        type: 'bar',
        data: orderData,
        yAxisIndex: 0,
        itemStyle: {
          color: '#67C23A'
        }
      },
      {
        name: '交易额',
        type: 'line',
        data: amountData,
        yAxisIndex: 1,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#E6A23C'
        },
        itemStyle: {
          color: '#E6A23C'
        }
      }
    ]
  }

  orderChart.setOption(option)
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  userChart?.resize()
  orderChart?.resize()
}

// 订单状态文本
const getOrderStatusText = (status: OrderStatus) => {
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
const getOrderStatusType = (status: OrderStatus) => {
  const typeMap: Record<OrderStatus, string> = {
    pending: 'info',
    paid: 'warning',
    completed: 'success',
    cancelled: 'danger',
    refunded: 'danger'
  }
  return typeMap[status] || 'info'
}

// 跳转到订单页面
const goToOrders = () => {
  router.push('/order')
}

// 跳转到商品页面
const goToProducts = () => {
  router.push('/product')
}

onMounted(() => {
  // 获取数据
  fetchStatistics()
  fetchRecentOrders()
  fetchHotProducts()

  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 销毁图表实例
  userChart?.dispose()
  orderChart?.dispose()

  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard-container {
  padding-bottom: 20px;
}

.statistic-card {
  height: 120px;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}

.statistic-title {
  font-size: 16px;
  color: #666;
  margin-bottom: 10px;
}

.statistic-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.statistic-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 60px;
  opacity: 0.2;
  color: #409EFF;
}

.product-icon {
  color: #67C23A;
}

.order-icon {
  color: #E6A23C;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 350px;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-info {
  display: flex;
  align-items: center;
}

.product-image {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  margin-right: 10px;
}

.product-detail {
  display: flex;
  flex-direction: column;
}

.product-name {
  font-weight: bold;
  margin-bottom: 3px;
}

.product-desc {
  font-size: 12px;
  color: #666;
}

.empty-data {
  padding: 30px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
