// profile.ts
export {};
const appInstance = getApp<IAppOption>();
import { login, getUserInfo, checkLogin, logout, getUserProfile, request } from '../../utils/util';

// 定义商品接口
interface Product {
  id: number;
  name: string;
  description: string;
  credits: number;
  price: number;
  image_url?: string;
  is_active: boolean;
  sort_order: number;
}

// 定义订单接口
interface Order {
  id: number;
  order_no: string;
  amount: number;
  credits: number;
  status: 'pending' | 'paid' | 'completed' | 'cancelled' | 'refunded';
  payment_id?: string;
  payment_time?: string;
}

Component({
  data: {
    isLoggedIn: false,
    userInfo: null as any,
    userId: 'user_123456',
    stats: {
      artworkCount: 0,
      likesCount: 0,
      credits: 0
    },
    // 积分兑换相关
    showActivateCardModal: false,
    cardKey: '',
    isActivating: false,
    // 商品相关
    products: [] as Product[],
    selectedProductId: null,
    isProcessingPayment: false
  },
  
  lifetimes: {
    attached() {
      // 检查登录状态
      this.checkLoginStatus();
    }
  },
  
  methods: {
    // 检查登录状态
    checkLoginStatus() {
      if (checkLogin()) {
        const userInfo = getUserInfo();
        this.setData({ 
          userInfo,
          stats: {
            artworkCount: userInfo.artworks_count || 0,
            likesCount: userInfo.likes_count || 0,
            credits: userInfo.credits || 0
          }
        });
        
        // 加载商品数据
        this.loadProducts();
      } else {
        this.setData({ userInfo: null });
      }
    },
    
    // 加载商品数据
    async loadProducts() {
      try {
        const products = await request('/products', 'GET', {
          limit: 4 // 限制只请求4个商品
        }) as Product[];
        
        this.setData({ products });
      } catch (error) {
        console.error('获取商品列表失败', error);
        // 获取商品失败不影响页面其他功能，只显示提示即可
        wx.showToast({
          title: '获取商品列表失败',
          icon: 'none'
        });
      }
    },
    
    // 登录（仅使用code）
    login() {
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      // 跳转到登录页面
      wx.navigateTo({
        url: '/pages/login/login'
      });
    },
    
    // 获取用户信息并登录
    getUserProfile() {
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      // 跳转到登录页面
      wx.navigateTo({
        url: '/pages/login/login'
      });
    },
    
    // 退出登录
    logout() {
      wx.showModal({
        title: '退出登录',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            logout();
            this.setData({ userInfo: null });
          }
        }
      });
    },
    
    // 导航到其他页面
    navigateTo(e: any) {
      const url = e.currentTarget.dataset.url;
      
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      // 检查是否需要登录
      const needLoginPages = ['/pages/credits/credits', '/pages/portfolio/portfolio'];
      if (needLoginPages.includes(url) && !this.data.userInfo) {
        wx.showModal({
          title: '需要登录',
          content: '请先登录以访问此功能',
          confirmColor: '#007aff',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({
                url: '/pages/login/login'
              });
            }
          }
        });
        return;
      }
      
      // 判断是否是 tabBar 页面
      const tabBarPages = ['/pages/gallery/gallery', '/pages/styles/styles', '/pages/create/create', '/pages/portfolio/portfolio'];
      if (tabBarPages.includes(url)) {
        wx.switchTab({ url });
      } else {
        wx.navigateTo({ url });
      }
    },

    onShow() {
      // 每次进入页面检查登录状态并加载数据
      this.setData({ isLoggedIn: checkLogin() });
      if (this.data.isLoggedIn) {
        this.loadUserData();
      } else {
        // 清理可能存在的旧数据
        this.setData({ userInfo: null, stats: { artworkCount: 0, likesCount: 0, credits: 0 } });
      }
    },

    // 加载用户数据和统计信息
    async loadUserData() {
      try {
        // 1. 获取用户基本信息 (/users/me)
        const userInfo = await request('/users/me', 'GET');
        this.setData({ userInfo });

        // 2. 获取积分余额 (/credits/balance)
        const creditsData = await request('/credits/balance', 'GET');
        this.setData({ 'stats.credits': creditsData.balance || 0 });

        // 3. 获取作品总数和获赞总数 (通过 /artworks 获取)
        // 注意：获取所有作品可能有效率问题，如果作品量大，后端最好提供专门的统计接口
        let artworkCount = 0;
        let likesCount = 0;
        const limit = 50; // 每次获取数量
        let skip = 0;
        let hasMore = true;

        while(hasMore) {
          const artworksData = await request(`/artworks?skip=${skip}&limit=${limit}`, 'GET');
          if (artworksData && artworksData.length > 0) {
            artworkCount += artworksData.length;
            likesCount += artworksData.reduce((sum: number, art: any) => sum + (art.likes_count || 0), 0);
            if (artworksData.length < limit) {
              hasMore = false;
            } else {
              skip += limit;
            }
          } else {
            hasMore = false;
          }
        }

        this.setData({
          'stats.artworkCount': artworkCount,
          'stats.likesCount': likesCount
        });

        // 4. 加载商品列表
        this.loadProducts();

      } catch (error) {
        console.error("加载用户数据失败:", error);
        wx.showToast({ title: '加载信息失败', icon: 'none' });
        // 如果获取用户信息失败，可能token失效，引导重新登录
        if ((error as any).statusCode === 401 || (error as any).statusCode === 403) {
          this.setData({ isLoggedIn: false, userInfo: null });
          logout(); // 清除本地无效token
        }
      }
    },

    // 跳转到登录页
    goToLogin() {
      wx.navigateTo({
        url: '/pages/login/login'
      });
    },

    // 跳转到我的积分页 (假设页面路径为 /pages/credits/credits)
    goToCredits() {
      wx.navigateTo({
        url: '/pages/profile/credits-history/credits-history'
      });
    },

    // 跳转到我的作品集页
    goToPortfolio() {
      wx.switchTab({ // 作品集是Tab页
        url: '/pages/portfolio/portfolio'
      });
    },
    
    // 跳转到订单查询页
    goToOrders() {
      wx.navigateTo({
        url: '/pages/profile/orders/orders'
      });
    },

    // 处理退出登录
    handleLogout() {
      wx.showModal({
        title: '提示',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            logout(); // 清除本地存储
            this.setData({ isLoggedIn: false, userInfo: null, stats: { artworkCount: 0, likesCount: 0, credits: 0 } });
            wx.showToast({ title: '已退出登录', icon: 'none' });
            // 跳转到登录页面
            wx.navigateTo({
              url: '/pages/login/login'
            });
          }
        }
      });
    },

    // 下拉刷新
    onPullDownRefresh() {
      if (this.data.isLoggedIn) {
        this.loadUserData().finally(() => {
          wx.stopPullDownRefresh();
        });
      } else {
        wx.stopPullDownRefresh();
      }
    },

    // 打开积分兑换弹窗
    showActivateCardModal() {
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      this.setData({
        showActivateCardModal: true,
        cardKey: ''
      });
    },
    
    // 关闭积分兑换弹窗
    hideActivateCardModal() {
      this.setData({
        showActivateCardModal: false
      });
    },
    
    // 阻止事件冒泡
    preventBubble() {
      // 阻止事件冒泡，防止点击模态框内容时关闭弹窗
      return;
    },
    
    // 处理卡密输入
    onCardKeyInput(e: any) {
      // 获取输入值并转为大写
      let value = e.detail.value.toUpperCase();
      
      // 移除非字母和数字字符
      value = value.replace(/[^A-Z0-9]/g, '');
      
      this.setData({
        cardKey: value
      });
    },
    
    // 激活卡密
    activateCardKey() {
      // 检查卡密长度
      if (this.data.cardKey.length !== 9) {
        wx.showToast({
          title: '请输入9位卡密',
          icon: 'none'
        });
        return;
      }
      
      // 设置激活中状态
      this.setData({
        isActivating: true
      });
      
      // 调用卡密激活API
      request('/card-keys/activate', 'POST', {
        card_key: this.data.cardKey
      })
        .then((res: any) => {
          // 激活成功
          this.hideActivateCardModal();
          
          // 显示成功提示，包含增加的积分信息
          wx.showModal({
            title: '兑换成功',
            content: `成功获得${res.credits}积分，当前余额${res.balance}积分`,
            showCancel: false,
            confirmText: '知道了',
            success: () => {
              // 更新积分显示
              this.setData({
                'stats.credits': res.balance
              });
            }
          });
        })
        .catch((error: any) => {
          // 处理错误情况
          let errorMessage = '卡密激活失败';
          
          if (error.detail) {
            errorMessage = typeof error.detail === 'string' 
              ? error.detail 
              : '卡密激活失败，请稍后重试';
          }
          
          wx.showToast({
            title: errorMessage,
            icon: 'none',
            duration: 2000
          });
        })
        .finally(() => {
          // 无论成功失败，都重置激活中状态
          this.setData({
            isActivating: false
          });
        });
    },
    
    // 选择商品
    selectProduct(e: any) {
      const productId = e.currentTarget.dataset.id;
      
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      this.setData({
        selectedProductId: productId
      });
    },
    
    // 处理支付 - 实现完整的支付流程
    async handlePayment() {
      if (!this.data.selectedProductId || this.data.isProcessingPayment) {
        return;
      }
      
      // 获取选中的商品
      const product = this.data.products.find((p) => p.id === this.data.selectedProductId);
      if (!product) {
        wx.showToast({ title: '请选择商品', icon: 'none' });
        return;
      }
      
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      // 设置支付处理中状态
      this.setData({ isProcessingPayment: true });
      
      try {
        // 步骤1：创建订单
        wx.showLoading({ title: '创建订单...', mask: true });
        const orderResult = await request('/orders/create', 'POST', {
          product_id: product.id
        }) as { order_id: number };
        
        const orderId = orderResult.order_id;
        
        // 步骤2：获取支付参数
        wx.showLoading({ title: '获取订单信息...', mask: true });
        const paymentResult = await request(`/orders/pay/${orderId}`, 'POST') as {
          payment_data: {
            timeStamp: string;
            nonceStr: string;
            packageValue: string;
            signType: 'MD5' | 'HMAC-SHA256' | 'RSA';
            paySign: string;
          }
        };
        
        // 步骤3：调用微信支付API
        wx.hideLoading();
        const paymentData = paymentResult.payment_data;
        
        wx.requestPayment({
          timeStamp: paymentData.timeStamp,
          nonceStr: paymentData.nonceStr,
          package: paymentData.packageValue, // 注意API里返回的是packageValue，而wx.requestPayment需要的是package
          signType: paymentData.signType,
          paySign: paymentData.paySign,
          success: (res) => {
            console.log('支付成功', res);
            
            // 查询订单状态确认
            this.checkOrderStatus(orderId);
          },
          fail: (err) => {
            console.error('支付失败', err);
            
            if (err.errMsg.indexOf('cancel') > -1) {
              wx.showToast({ title: '您已取消支付', icon: 'none' });
            } else {
              wx.showToast({ title: '支付失败', icon: 'none' });
            }
            
            // 重置支付处理状态
            this.setData({ isProcessingPayment: false });
            
            // 即使失败也检查一次订单状态，以防前端判断错误
            this.checkOrderStatus(orderId);
          }
        });
      } catch (error: any) {
        console.error('处理支付流程失败', error);
        this.setData({ isProcessingPayment: false });
        
        wx.hideLoading();
        wx.showToast({ 
          title: (error.detail as string) || '创建订单失败，请稍后再试',
          icon: 'none' 
        });
      }
    },
    
    // 检查订单状态
    async checkOrderStatus(orderId: number) {
      // 显示加载提示
      wx.showLoading({ title: '确认订单状态...', mask: true });
      
      // 轮询支付状态，最多尝试5次
      let retryCount = 0;
      const maxRetries = 5;
      const checkInterval = 2000; // 每秒检查一次
      
      const checkStatus = async () => {
        try {
          // 使用新的支付状态查询API
          const result = await request(`/orders/payment-status/${orderId}`, 'GET') as {
            order_id: number;
            status: string;
            paid: boolean;
            message: string;
          };
          
          if (result.paid) {
            // 支付成功
            wx.hideLoading();
            
            // 更新积分显示
            const orderDetails = await request(`/orders/${orderId}`, 'GET') as Order;
            
            this.setData({
              'stats.credits': (this.data.stats.credits || 0) + orderDetails.credits,
              selectedProductId: null,
              isProcessingPayment: false
            });
            
            // 显示成功提示
            wx.showModal({
              title: '购买成功',
              content: `成功购买${orderDetails.credits}积分，当前余额${this.data.stats.credits}积分`,
              showCancel: false,
              confirmText: '知道了'
            });
            
            return; // 成功后终止轮询
          } else if (result.status === 'cancelled' || result.status === 'refunded') {
            // 支付取消或退款
            wx.hideLoading();
            wx.showModal({
              title: '支付未完成',
              content: result.message || '订单已取消或退款',
              showCancel: false,
              confirmText: '知道了'
            });
            this.setData({ isProcessingPayment: false });
            return; // 终止轮询
          } else {
            // 订单处理中，继续轮询
            retryCount++;
            if (retryCount < maxRetries) {
              setTimeout(checkStatus, checkInterval);
            } else {
              // 超过最大重试次数
              wx.hideLoading();
              wx.showModal({
                title: '订单处理中',
                content: '支付可能正在处理中，请稍后在"订单查询"中查看结果',
                showCancel: false,
                confirmText: '知道了'
              });
              this.setData({ isProcessingPayment: false });
            }
          }
        } catch (error) {
          console.error('查询支付状态失败', error);
          retryCount++;
          
          if (retryCount < maxRetries) {
            setTimeout(checkStatus, checkInterval);
          } else {
            wx.hideLoading();
            wx.showModal({
              title: '支付状态未知',
              content: '无法确认支付状态，请在"订单查询"中确认是否支付成功',
              showCancel: false,
              confirmText: '知道了'
            });
            this.setData({ isProcessingPayment: false });
          }
        }
      };
      
      // 开始检查订单状态，微信支付完成后立即开始检查
      checkStatus();
    }
  }
})