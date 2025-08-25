import { request, checkLogin, logout } from '../../../utils/util';

// 定义订单接口
interface Order {
  id: number;
  order_no: string;
  user_id: number;
  product_id: number;
  amount: number;
  credits: number;
  status: 'pending' | 'paid' | 'completed' | 'cancelled' | 'refunded';
  payment_id?: string;
  payment_time?: string;
  refund_time?: string;
  remark?: string;
  created_at: string;
  updated_at: string;
}

// 订单列表响应接口
interface OrderListResponse {
  data: Order[];
  total: number;
  has_more: boolean;
}

Component({
  data: {
    orders: [] as Order[],
    isLoading: false,
    hasMoreOrders: true,
    currentPage: 1,
    pageSize: 10,
    statusText: {
      'pending': '处理中',
      'paid': '已支付',
      'completed': '成功',
      'cancelled': '已取消',
      'refunded': '已退款'
    }
  },
  
  lifetimes: {
    attached() {
      // 检查登录状态
      if (!checkLogin()) {
        wx.showModal({
          title: '提示',
          content: '请先登录',
          showCancel: false,
          success: () => {
            wx.navigateBack();
          }
        });
        return;
      }
      
      // 加载订单数据
      this.loadOrders();
    }
  },
  
  methods: {
    // 加载订单数据
    async loadOrders(page = 1) {
      if (this.data.isLoading) return;
      
      this.setData({ isLoading: true });
      
      try {
        const orders = await request(
          `/orders?page=${page}&limit=${this.data.pageSize}&sort=-created_at`,
          'GET'
        ) as Order[];
        
        // 格式化日期和金额
        const formattedOrders = orders.map((order: Order) => ({
          ...order,
          created_at: this.formatDate(order.created_at)
        }));
        
        // 更新数据
        if (page === 1) {
          this.setData({ orders: formattedOrders });
        } else {
          this.setData({ orders: [...this.data.orders, ...formattedOrders] });
        }
        
        // 是否有更多数据
        this.setData({
          hasMoreOrders: orders.length === this.data.pageSize, // 如果返回的数量等于pageSize，假设有更多数据
          currentPage: page
        });
      } catch (error) {
        console.error('加载订单失败', error);
        
        // 处理未授权情况
        if ((error as any).statusCode === 401 || (error as any).statusCode === 403) {
          logout();
          wx.showModal({
            title: '提示',
            content: '登录已过期，请重新登录',
            showCancel: false,
            success: () => {
              wx.navigateBack();
            }
          });
        } else {
          wx.showToast({ title: '加载失败，请重试', icon: 'none' });
        }
      } finally {
        this.setData({ isLoading: false });
      }
    },
    
    // 加载更多订单
    loadMoreOrders() {
      if (this.data.hasMoreOrders && !this.data.isLoading) {
        this.loadOrders(this.data.currentPage + 1);
      }
    },
    
    // 格式化日期
    formatDate(dateString: string) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      
      // 获取年月日时分
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    },
    
    // 下拉刷新
    onPullDownRefresh() {
      this.loadOrders().finally(() => {
        wx.stopPullDownRefresh();
      });
    },
    
    // 页面上拉触底
    onReachBottom() {
      this.loadMoreOrders();
    }
  }
}); 