import { formatTime, request } from '../../../utils/util';

// 每页记录数
const PAGE_SIZE = 10;

Page({
  data: {
    balance: 0,
    records: [] as any[],
    skip: 0,
    limit: PAGE_SIZE,
    hasMore: true,
    loading: true,
    loadingMore: false
  },

  onLoad() {
    // 加载初始数据
    this.loadBalance();
    this.loadRecords();
  },

  // 加载积分余额
  async loadBalance() {
    try {
      const result = await request('/credits/balance', 'GET');
      if (result && result.balance !== undefined) {
        this.setData({ balance: result.balance });
      }
    } catch (error) {
      console.error('获取积分余额失败:', error);
      wx.showToast({ title: '获取积分余额失败', icon: 'none' });
    }
  },

  // 加载积分记录
  async loadRecords(append = false) {
    if (!append) {
      this.setData({ 
        loading: true,
        skip: 0,
        records: []
      });
    } else {
      this.setData({ loadingMore: true });
    }

    try {
      const skip = append ? this.data.skip : 0;
      const result = await request(`/credits/records?skip=${skip}&limit=${this.data.limit}`, 'GET');
      
      if (Array.isArray(result)) {
        // 格式化日期
        const formattedRecords = result.map(record => ({
          ...record,
          created_at: formatTime(new Date(record.created_at))
        }));

        if (append) {
          // 追加数据
          this.setData({
            records: [...this.data.records, ...formattedRecords],
            skip: skip + formattedRecords.length,
            hasMore: formattedRecords.length >= PAGE_SIZE
          });
        } else {
          // 重置数据
          this.setData({
            records: formattedRecords,
            skip: formattedRecords.length,
            hasMore: formattedRecords.length >= PAGE_SIZE
          });
        }
      } else {
        this.setData({ hasMore: false });
        console.error('获取积分记录格式错误:', result);
      }
    } catch (error) {
      console.error('获取积分记录失败:', error);
      wx.showToast({ title: '获取积分记录失败', icon: 'none' });
    } finally {
      this.setData({ 
        loading: false,
        loadingMore: false
      });
    }
  },

  // 加载更多记录
  loadMore() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadRecords(true);
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    Promise.all([
      this.loadBalance(),
      this.loadRecords()
    ]).finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 到达页面底部
  onReachBottom() {
    this.loadMore();
  }
}); 