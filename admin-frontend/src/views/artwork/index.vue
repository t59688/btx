<template>
  <div class="artwork-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>作品管理</span>
        </div>
      </template>

      <!-- 搜索和筛选区域 -->
      <div class="filter-container">
        <el-input
          v-model="queryParams.id"
          placeholder="请输入作品ID"
          style="width: 200px;"
          class="filter-item"
          @keyup.enter="handleSearch"
        />

        <el-select
          v-model="queryParams.status"
          placeholder="处理状态"
          clearable
          style="width: 130px"
          class="filter-item"
        >
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>

        <el-select
          v-model="queryParams.is_public"
          placeholder="是否公开"
          clearable
          style="width: 130px"
          class="filter-item"
        >
          <el-option label="公开" :value="true" />
          <el-option label="私密" :value="false" />
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

      <!-- 作品表格 -->
      <el-table
        v-loading="loading"
        :data="artworkList"
        style="width: 100%;"
        border
        :max-height="windowHeight - 220"
        class="artwork-table"
        stripe
        highlight-current-row
      >
        <el-table-column
          type="index"
          width="60"
          align="center"
          fixed="left"
        />

        <el-table-column
          prop="id"
          label="ID"
          width="80"
          align="center"
          fixed="left"
        />

        <el-table-column
          label="图片"
          min-width="280"
          align="center"
        >
          <template #default="{ row }">
            <div class="image-previews">
              <el-image
                style="width: 120px; height: 120px; margin-right: 15px;"
                :src="row.source_image_url"
                fit="cover"
                :preview-src-list="[row.source_image_url]"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>

              <el-icon class="transform-icon"><Right /></el-icon>

              <el-image
                style="width: 120px; height: 120px;"
                :src="row.result_image_url"
                fit="cover"
                :preview-src-list="row.result_image_url ? [row.result_image_url] : []"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          label="用户"
          min-width="180"
        >
          <template #default="{ row }">
            <div v-if="row.user" class="user-info">
              <el-avatar
                :size="36"
                :src="row.user.avatar_url"
              >
                {{ row.user.nickname?.charAt(0) }}
              </el-avatar>
              <span class="nickname">{{ row.user.nickname }}</span>
            </div>
            <span v-else>未知用户</span>
          </template>
        </el-table-column>

        <el-table-column
          label="风格"
          min-width="150"
        >
          <template #default="{ row }">
            <el-tag v-if="row.style">{{ row.style.name }}</el-tag>
            <span v-else>未知风格</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="status"
          label="状态"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="is_public"
          label="是否公开"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-switch
              v-model="row.is_public"
              @change="handlePublicChange(row)"
              active-color="#13ce66"
              inactive-color="#ff4949"
              style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949;"
            />
          </template>
        </el-table-column>

        <el-table-column
          prop="likes_count"
          label="点赞数"
          min-width="100"
          align="center"
        />

        <el-table-column
          prop="views_count"
          label="查看数"
          min-width="100"
          align="center"
        />

        <el-table-column
          prop="created_at"
          label="创建时间"
          min-width="180"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column
          label="操作"
          fixed="right"
          min-width="150"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              :icon="View"
              @click="handleViewDetail(row)"
            >
              查看
            </el-button>

            <el-button
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
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
          background
        />
      </div>
    </el-card>

    <!-- 作品详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="作品详情"
      width="80%"
      top="5vh"
    >
      <div v-if="selectedArtwork" class="artwork-detail">
        <!-- 图片展示 -->
        <div class="artwork-images">
          <div class="image-item">
            <h4>原图</h4>
            <el-image
              :src="selectedArtwork.source_image_url"
              fit="contain"
              style="width: 100%; max-height: 400px;"
              :preview-src-list="[selectedArtwork.source_image_url]"
            />
          </div>

          <div class="image-item">
            <h4>结果图</h4>
            <el-image
              v-if="selectedArtwork.result_image_url"
              :src="selectedArtwork.result_image_url"
              fit="contain"
              style="width: 100%; max-height: 400px;"
              :preview-src-list="[selectedArtwork.result_image_url]"
            />
            <div v-else class="no-result">
              <el-icon><Picture /></el-icon>
              <span>暂无结果图</span>
            </div>
          </div>
        </div>

        <!-- 作品信息 -->
        <div class="artwork-info">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="ID">{{ selectedArtwork.id }}</el-descriptions-item>
            <el-descriptions-item label="用户">
              <div v-if="selectedArtwork.user" class="user-info">
                <el-avatar
                  :size="36"
                  :src="selectedArtwork.user.avatar_url"
                >
                  {{ selectedArtwork.user.nickname?.charAt(0) }}
                </el-avatar>
                <span class="nickname">{{ selectedArtwork.user.nickname }}</span>
              </div>
              <span v-else>未知用户</span>
            </el-descriptions-item>

            <el-descriptions-item label="风格">
              {{ selectedArtwork.style?.name || '未知风格' }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(selectedArtwork.status)">
                {{ getStatusText(selectedArtwork.status) }}
              </el-tag>
            </el-descriptions-item>

            <el-descriptions-item label="是否公开">
              <el-switch
                v-model="selectedArtwork.is_public"
                @change="handlePublicChange(selectedArtwork)"
                active-color="#13ce66"
                inactive-color="#ff4949"
                style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949;"
              />
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(selectedArtwork.created_at) }}
            </el-descriptions-item>

            <el-descriptions-item label="点赞数">
              {{ selectedArtwork.likes_count }}
            </el-descriptions-item>
            <el-descriptions-item label="查看数">
              {{ selectedArtwork.views_count }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="selectedArtwork.status === 'failed'" class="error-message">
            <h4>错误信息</h4>
            <el-alert
              :title="selectedArtwork.error_message || '未知错误'"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="danger" @click="handleDelete(selectedArtwork)">删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, View, Delete, Picture, Right } from '@element-plus/icons-vue'
import { getArtworks, getArtworkDetail, updateArtwork, deleteArtwork } from '@/api/artwork'
import type { Artwork } from '@/api/artwork'

// 加载状态
const loading = ref(false)

// 作品列表数据
const artworkList = ref<Artwork[]>([])
const total = ref(0)

// 查询参数
const queryParams = reactive({
  page: 1,
  limit: 20,
  skip: 0,
  id: '',
  status: '',
  is_public: undefined as boolean | undefined
})

// 作品详情对话框
const detailDialogVisible = ref(false)
const selectedArtwork = ref<Artwork | null>(null)

// 监听窗口高度变化，用于自适应表格高度
const windowHeight = ref(window.innerHeight)
const handleResize = () => {
  windowHeight.value = window.innerHeight
}

// 获取作品列表
const getArtworkList = async () => {
  try {
    loading.value = true
    queryParams.skip = (queryParams.page - 1) * queryParams.limit

    const params: any = { ...queryParams }
    // 处理ID查询 - 转换为数字或移除
    if (params.id) {
      const idNum = parseInt(params.id)
      if (!isNaN(idNum)) {
        params.id = idNum
      } else {
        delete params.id
      }
    } else {
      delete params.id
    }

    const response = await getArtworks(params)
    console.log('API返回作品数据:', response) // 调试日志

    // 处理数组形式的响应
    if (Array.isArray(response)) {
      artworkList.value = response.map(enrichArtworkData)
      total.value = response.length
    }
    // 处理分页格式的响应 {items: [], total: 0}
    else if (response && typeof response === 'object' && 'items' in response) {
      artworkList.value = (response.items || []).map(enrichArtworkData)
      total.value = response.total || 0
    }
    // 处理可能的其他格式响应
    else {
      artworkList.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取作品列表失败:', error)
    artworkList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 增强作品数据，处理关联数据
const enrichArtworkData = (artwork: Artwork): Artwork => {
  // 处理用户关联数据
  if (!artwork.user && artwork.user_id) {
    // 如果API没有返回user对象但有user_id，添加一个占位符
    artwork.user = {
      nickname: `用户${artwork.user_id}`,
      avatar_url: ''
    }
  }

  // 处理风格关联数据
  if (!artwork.style && artwork.style_id) {
    // 如果API没有返回style对象但有style_id，添加一个占位符
    artwork.style = {
      name: `风格${artwork.style_id}`,
      category: ''
    }
  }

  return artwork
}

// 搜索按钮点击事件
const handleSearch = () => {
  queryParams.page = 1
  getArtworkList()
}

// 重置查询条件
const resetQuery = () => {
  queryParams.id = ''
  queryParams.status = ''
  queryParams.is_public = undefined
  queryParams.page = 1
  getArtworkList()
}

// 查看作品详情
const handleViewDetail = async (row: Artwork) => {
  try {
    // 重新获取完整作品信息
    const response = await getArtworkDetail(row.id)
    selectedArtwork.value = enrichArtworkData(response)
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取作品详情失败:', error)
    ElMessage.error('获取作品详情失败')
  }
}

// 处理是否公开状态变更
const handlePublicChange = async (row: Artwork) => {
  try {
    await updateArtwork(row.id, { is_public: row.is_public })
    ElMessage.success(`已${row.is_public ? '公开' : '设为私密'}`)
  } catch (error) {
    console.error('更新作品状态失败:', error)
    // 恢复原始状态
    row.is_public = !row.is_public
    ElMessage.error('更新失败，请稍后重试')
  }
}

// 处理删除作品
const handleDelete = (row: Artwork | null) => {
  if (!row) return

  ElMessageBox.confirm(
    `确定要删除该作品吗？删除后无法恢复。`,
    '删除作品',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteArtwork(row.id)
      ElMessage.success('删除成功')

      // 如果是从详情页删除，关闭详情页
      if (detailDialogVisible.value) {
        detailDialogVisible.value = false
      }

      // 重新加载列表
      getArtworkList()
    } catch (error) {
      console.error('删除作品失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }).catch(() => {})
}

// 分页处理
const handleSizeChange = (size: number) => {
  queryParams.limit = size
  queryParams.page = 1
  getArtworkList()
}

const handleCurrentChange = (page: number) => {
  queryParams.page = page
  getArtworkList()
}

// 获取状态样式
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
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

// 页面加载时获取作品列表
onMounted(() => {
  getArtworkList()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.artwork-container {
  width: 100%;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 18px;
    font-weight: bold;
  }

  .filter-container {
    margin-bottom: 25px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
  }

  .artwork-table {
    margin-bottom: 30px;

    // 调整表格字体大小和行距
    :deep(.el-table__row) {
      line-height: 1.6;
    }

    :deep(.el-table__header th) {
      font-size: 16px;
      font-weight: bold;
      background-color: #f5f7fa;
      color: #333;
    }

    .image-previews {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 0;

      .transform-icon {
        font-size: 24px;
        margin: 0 15px;
        color: #409EFF;
      }
    }

    .image-error {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      background-color: #f5f7fa;
      color: #909399;
      font-size: 24px;
    }

    .user-info {
      display: flex;
      align-items: center;

      .nickname {
        margin-left: 15px;
        max-width: 130px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 16px;
      }

      @media (min-width: 1600px) {
        .nickname {
          max-width: 200px;
        }
      }
    }
  }

  .pagination-container {
    margin-top: 30px;
    display: flex;
    justify-content: center;
  }
}

.artwork-detail {
  .artwork-images {
    display: flex;
    gap: 30px;
    margin-bottom: 30px;

    .image-item {
      flex: 1;

      h4 {
        font-size: 18px;
        margin-top: 0;
        margin-bottom: 15px;
      }

      .no-result {
        height: 400px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background-color: #f5f7fa;
        color: #909399;
        font-size: 18px;

        .el-icon {
          font-size: 48px;
          margin-bottom: 15px;
        }
      }
    }
  }

  .artwork-info {
    .error-message {
      margin-top: 25px;

      h4 {
        font-size: 18px;
        margin-top: 0;
        margin-bottom: 15px;
      }
    }
  }

  :deep(.el-descriptions__label) {
    font-size: 16px;
    font-weight: bold;
  }

  :deep(.el-descriptions__content) {
    font-size: 16px;
  }
}
</style>
