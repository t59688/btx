import { login, getUserInfo, checkLogin, request, logout } from '../../utils/util';

export {};
const appInstance = getApp<IAppOption>();

// 作品状态枚举
enum ArtworkStatus {
  Processing = 'processing',
  Completed = 'completed',
  Failed = 'failed'
}

Component({
  properties: {},
  data: {
    isLoggedIn: false,
    userInfo: null as any,
    activeTab: 'all',
    portfolio: [] as any[],
    skip: 0,
    limit: 10,
    isLoading: false,
    noMoreData: false,
    isRefreshing: false,
    progressCheckTimer: null as any, // 进度检查定时器
    processingArtworks: [] as string[], // 存储处理中的作品ID
    sliderPositions: {} as Record<string, number>, // 存储每个作品的滑动位置
    currentSliderId: null as string | null, // 当前正在滑动的分割线ID
  },
  
  lifetimes: {
    attached() {
      this.setData({ isLoggedIn: checkLogin() });
      if (this.data.isLoggedIn) {
        this.setData({ userInfo: getUserInfo() });
        this.loadPortfolio(true);
      }
    },
    detached() {
      // 组件销毁时清除定时器
      if (this.data.progressCheckTimer) {
        clearInterval(this.data.progressCheckTimer);
      }
    }
  },
  
  pageLifetimes: {
    show() {
      const loggedIn = checkLogin();
      const userInfoChanged = loggedIn && JSON.stringify(this.data.userInfo) !== JSON.stringify(getUserInfo());
      
      if (loggedIn !== this.data.isLoggedIn || userInfoChanged) {
        this.setData({ 
          isLoggedIn: loggedIn,
          userInfo: loggedIn ? getUserInfo() : null 
        });
        if (loggedIn) {
          this.loadPortfolio(true);
        } else {
          this.setData({ portfolio: [], skip: 0, noMoreData: false, isLoading: false });
          // 清除定时器
          if (this.data.progressCheckTimer) {
            clearInterval(this.data.progressCheckTimer);
            this.setData({ progressCheckTimer: null });
          }
        }
      } else if (this.data.isLoggedIn && this.data.portfolio.length === 0 && !this.data.isLoading) {
        this.loadPortfolio(true);
      }
    },
    hide() {
      // 页面隐藏时清除定时器
      if (this.data.progressCheckTimer) {
        clearInterval(this.data.progressCheckTimer);
        this.setData({ progressCheckTimer: null });
      }
    }
  },
  
  methods: {
    // 重新生成作品
    regenerateArtwork(e: any) {
      wx.vibrateShort({ type: 'light' });
      const id = e.currentTarget.dataset.id;
      const item = this.data.portfolio.find(artwork => artwork.id === id);
      
      if (item && item.sourceImageUrl) {
        // 将原始图片URL存储到全局数据
        const app = getApp<IAppOption>();
        app.globalData = app.globalData || {};
        app.globalData.regenerateImageUrl = item.sourceImageUrl;
        
        // 跳转到创建页面
        wx.switchTab({
          url: '/pages/create/create',
          success: () => {
            console.log('跳转到创建页面成功');
          },
          fail: (err) => {
            console.error('跳转到创建页面失败:', err);
            wx.showToast({ title: '跳转失败，请手动前往创建页面', icon: 'none' });
          }
        });
      } else {
        wx.showToast({ title: '获取原图失败', icon: 'none' });
      }
    },

    // 加载作品集数据
    loadPortfolio(refresh = false) {
      if (this.data.isLoading) return;
      if (!refresh && this.data.noMoreData) return;
      
      this.setData({ isLoading: true });
      
      if (refresh) {
        this.setData({ skip: 0, noMoreData: false, portfolio: [] });
      }
      
      const queryParams: any = {
        skip: this.data.skip,
        limit: this.data.limit,
        order_by: 'created_at',
        order_desc: true
      };
      
      if (this.data.activeTab === 'public') {
        queryParams.is_public = true;
      } else if (this.data.activeTab === 'private') {
        queryParams.is_public = false;
      }
      
      const queryString = Object.keys(queryParams)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(queryParams[key])}`)
        .join('&');
      
      request(`/artworks?${queryString}`, 'GET')
        .then(data => {
          const artworks = data || [];
          const noMore = artworks.length < this.data.limit;
          const formattedArtworks = artworks.map((item: any) => ({
            id: item.id,
            sourceImageUrl: item.source_image_url || '',
            resultImageUrl: item.result_image_url ? `${item.result_image_url}?imageMogr2/thumbnail/!40p` : '',
            styleName: item.style_name || '未知风格',
            createTime: this.formatDate(item.created_at),
            isPublic: item.is_public,
            publicScope: item.public_scope || 'result_only', // 添加公开范围字段
            status: item.status
          }));
          
          // 对于新加载的作品，初始化滑动位置为50%
          const newSliderPositions = { ...this.data.sliderPositions };
          formattedArtworks.forEach((item: {id: string}) => {
            if (!newSliderPositions[item.id]) {
              newSliderPositions[item.id] = 50;
            }
          });
          
          this.setData({
            portfolio: refresh ? formattedArtworks : [...this.data.portfolio, ...formattedArtworks],
            skip: this.data.skip + artworks.length,
            noMoreData: noMore,
            isLoading: false,
            isRefreshing: false,
            sliderPositions: newSliderPositions
          });
          
          // 收集处理中的作品ID
          this.collectProcessingArtworks();
        })
        .catch(err => {
          console.error('加载作品集失败:', err);
          wx.showToast({ title: '加载失败, 请稍后重试', icon: 'none' });
          this.setData({ isLoading: false, isRefreshing: false });
          if (err && (err.statusCode === 401 || err.statusCode === 403)) {
            logout();
            this.setData({ isLoggedIn: false, userInfo: null, portfolio: [] });
          }
        });
    },
    
    // 监听用户上拉触底事件
    onReachBottom() {
      if (!this.data.isLoading && !this.data.noMoreData) {
        console.log('Reach bottom, loading more...');
        this.loadMore();
      }
    },
    
    // 加载更多数据
    loadMore() {
      if (!this.data.isLoading && !this.data.noMoreData) {
        this.loadPortfolio(false);
      }
    },
    
    // 收集处理中的作品ID，并启动定时检查
    collectProcessingArtworks() {
      const processingArtworks = this.data.portfolio
        .filter(item => item.status === ArtworkStatus.Processing)
        .map(item => item.id);
      
      this.setData({ processingArtworks });
      
      // 如果有处理中的作品且没有定时器，则启动定时器
      if (processingArtworks.length > 0 && !this.data.progressCheckTimer) {
        const timer = setInterval(() => {
          this.checkAllProcessingArtworks();
        }, 5000); // 每5秒检查一次
        
        this.setData({ progressCheckTimer: timer });
      } 
      // 如果没有处理中的作品，但有定时器，则清除定时器
      else if (processingArtworks.length === 0 && this.data.progressCheckTimer) {
        clearInterval(this.data.progressCheckTimer);
        this.setData({ progressCheckTimer: null });
      }
    },
    
    // 检查所有处理中的作品
    checkAllProcessingArtworks() {
      const processingArtworks = this.data.processingArtworks;
      if (processingArtworks.length === 0) {
        if (this.data.progressCheckTimer) {
          clearInterval(this.data.progressCheckTimer);
          this.setData({ progressCheckTimer: null });
        }
        return;
      }
      
      // 检查每个处理中的作品
      processingArtworks.forEach((id: string) => {
        this.checkArtworkProgressSilently(id);
        });
    },
    
    // 设置作品公开/私密状态
    updateArtworkStatus(id: string, isPublic: boolean, publicScope?: string) {
      wx.vibrateShort({ type: 'light' });
      wx.showLoading({ title: '更新中...' });
      
      // 准备请求数据
      const requestData: any = { is_public: isPublic };
      
      // 如果是设为公开且指定了公开范围，添加public_scope字段
      if (isPublic && publicScope) {
        requestData.public_scope = publicScope;
      }
      
      // 使用PATCH请求更新作品状态
      request(`/artworks/${id}/publish`, 'PATCH', requestData)
        .then(data => {
          wx.hideLoading();
          const updatedArtwork = data;
          
          const portfolio = this.data.portfolio.map(item => {
            if (item.id === id) {
              return {
                ...item,
                isPublic: updatedArtwork.is_public,
                publicScope: updatedArtwork.public_scope // 更新公开范围
              };
            }
            return item;
          });
          
          let finalPortfolio = portfolio;
          if (this.data.activeTab === 'public' && !isPublic) {
            finalPortfolio = portfolio.filter(item => item.id !== id);
          } else if (this.data.activeTab === 'private' && isPublic) {
            finalPortfolio = portfolio.filter(item => item.id !== id);
          }

          this.setData({ portfolio: finalPortfolio });
          wx.showToast({ title: isPublic ? '已设为公开' : '已设为私密', icon: 'success' });
        })
        .catch(err => {
          wx.hideLoading();
          console.error('更新作品状态失败:', err);
          wx.showToast({ title: '更新失败，请重试', icon: 'none' });
        });
    },
    
    // 删除作品
    deleteArtwork(id: string) {
      wx.vibrateShort({ type: 'light' });
      wx.showModal({
        title: '确认删除',
        content: '您确定要删除此作品吗？此操作无法撤销。',
        confirmText: '删除',
        confirmColor: '#ff3b30',
        cancelColor: '#007aff',
        success: (res) => {
          if (res.confirm) {
            wx.showLoading({ title: '删除中...' });
            request(`/artworks/${id}`, 'DELETE')
              .then(() => {
                wx.hideLoading();
                const portfolio = this.data.portfolio.filter(item => item.id !== id);
                const sliderPositions = { ...this.data.sliderPositions };
                delete sliderPositions[id];
                
                this.setData({ portfolio, sliderPositions });
                wx.showToast({ title: '删除成功', icon: 'success' });
                
                // 更新处理中的作品列表
                this.collectProcessingArtworks();
              })
              .catch(err => {
                wx.hideLoading();
                console.error('删除作品失败:', err);
                wx.showToast({ title: '删除失败，请重试', icon: 'none' });
              });
          }
        }
      });
    },
    
    // 检查单个作品的进度（带加载提示）
    checkArtworkProgress(id: string) {
      request(`/artworks/${id}/progress`, 'GET')
        .then(data => {
          if (data.status === ArtworkStatus.Completed) {
            wx.showToast({ title: '作品处理完成', icon: 'success' });
            this.loadPortfolio(true);
          } else if (data.status === ArtworkStatus.Failed) {
            wx.showToast({ title: `处理失败: ${data.error_message || '未知错误'}`, icon: 'none' });
            const portfolio = this.data.portfolio.map(item => item.id === id ? {...item, status: 'failed'} : item);
            this.setData({portfolio});
            // 更新处理中的作品列表
            this.collectProcessingArtworks();
          } else {
            wx.showToast({ title: `处理中 (${data.progress || 0}%)`, icon: 'loading', duration: 1500 });
          }
        })
        .catch(err => {
          console.error('获取作品进度失败:', err);
          wx.showToast({ title: '查询进度失败', icon: 'none' });
        });
    },
    
    // 静默检查单个作品的进度（无加载提示）
    checkArtworkProgressSilently(id: string) {
      request(`/artworks/${id}/progress`, 'GET')
        .then(data => {
          // 查找当前作品在数组中的索引
          const index = this.data.portfolio.findIndex(item => item.id === id);
          if (index === -1) return; // 未找到作品，可能已被删除
          
          if (data.status === ArtworkStatus.Completed) {
            // 作品已完成，更新数据
            const updatedPortfolio = [...this.data.portfolio];
            updatedPortfolio[index] = {
              ...updatedPortfolio[index],
              status: ArtworkStatus.Completed,
              resultImageUrl: data.artwork_url || updatedPortfolio[index].resultImageUrl
            };
            
            this.setData({ portfolio: updatedPortfolio });
            // 更新处理中的作品列表
            this.collectProcessingArtworks();
          } else if (data.status === ArtworkStatus.Failed) {
            // 作品处理失败
            const updatedPortfolio = [...this.data.portfolio];
            updatedPortfolio[index] = {
              ...updatedPortfolio[index],
              status: ArtworkStatus.Failed
            };
            
            this.setData({ portfolio: updatedPortfolio });
            // 更新处理中的作品列表
            this.collectProcessingArtworks();
          } else {
            // 作品仍在处理中，更新进度
            const updatedPortfolio = [...this.data.portfolio];
            updatedPortfolio[index] = {
              ...updatedPortfolio[index],
              progress: data.progress || 0
            };
            
            this.setData({ portfolio: updatedPortfolio });
          }
        })
        .catch(err => {
          console.error('静默获取作品进度失败:', err);
        });
    },
    
    // 根据风格名称获取颜色
    getStyleColor(styleName: string): string {
      const styleColors: Record<string, string> = {
        '水墨国风': '#3b3a39',
        '油画': '#2c7873',
        '赛博朋克': '#7209b7',
        '动漫风': '#3a86ff',
        '波普艺术': '#f72585'
      };
      
      return styleColors[styleName] || '#8e8e93';
    },
    
    // 格式化日期
    formatDate(dateString: string): string {
      if (!dateString) return '';
      try {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now.getTime() - date.getTime());
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 1 && date.getDate() === now.getDate()) {
          return `今天 ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else if (diffDays < 2 && date.getDate() === now.getDate() - 1) {
          return `昨天 ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else if (diffDays < 7) {
          const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
          return `${weekdays[date.getDay()]} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else if (date.getFullYear() === now.getFullYear()) {
          return `${date.getMonth() + 1}月${date.getDate()}日`;
        } else {
          return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
        }
      } catch (e) {
        console.error("日期格式化错误:", dateString, e);
        return dateString;
      }
    },
    
    // 登录
    login() {
      wx.vibrateShort({ type: 'light' });
      wx.navigateTo({ url: '/pages/login/login' });
    },
    
    // 切换标签
    switchTab(e: any) {
      const tab = e.currentTarget.dataset.tab;
      if (this.data.activeTab !== tab) {
        wx.vibrateShort({ type: 'light' });
        this.setData({ activeTab: tab });
        this.loadPortfolio(true);
      }
    },
    
    // 查看作品详情 (已废弃，但保留以防万一)
    viewDetail(e: any) {
      const id = e.currentTarget.dataset.id;
      wx.vibrateShort({ type: 'light' });
      
      const artwork = this.data.portfolio.find(item => item.id === id);
      if (artwork && artwork.status === ArtworkStatus.Processing) {
        wx.showToast({ title: '作品正在处理中...', icon: 'loading', duration: 1500 });
        return;
      }
      if (artwork && artwork.status === ArtworkStatus.Failed) {
        wx.showToast({ title: '作品处理失败', icon: 'none'});
        return;
      }
      
      // 检查是否是长按
      if (e.type === 'longpress') {
        this.handleLongPressArtwork(e);
        return;
      }
      
      // 使用图片预览API
      if (artwork && artwork.resultImageUrl) {
        wx.previewImage({
          current: artwork.resultImageUrl, // 当前显示图片的链接
          urls: [artwork.resultImageUrl], // 需要预览的图片链接列表
          showmenu: true // 显示长按菜单
        });
      } else {
        wx.showToast({ title: '图片不存在', icon: 'none' });
      }
    },
    
    // 处理长按作品事件
    handleLongPressArtwork(e: any) {
      const id = e.currentTarget.dataset.id;
      wx.vibrateShort({ type: 'medium' });
      
      // 找到要操作的作品
      const artwork = this.data.portfolio.find(item => item.id === id);
      if (!artwork || artwork.status !== ArtworkStatus.Completed) {
        return; // 只处理已完成状态的作品
      }
      
      // 构建菜单选项
      const itemList = [  '预览','保存效果图到相册','保存原图到相册'];
      
      wx.showActionSheet({
        itemList: itemList,
        success: (res) => {
          if (res.tapIndex === 0 && artwork.sourceImageUrl) {
            // 保存原图到相册
            const originalUrl = artwork.sourceImageUrl.split('?')[0];
            this.saveOriginalImage(originalUrl);
          } else if (res.tapIndex === 1 && artwork.resultImageUrl) {
            // 保存效果图到相册
            const originalUrl = artwork.resultImageUrl.split('?')[0];
            this.saveOriginalImage(originalUrl);
          } else if (res.tapIndex === 2) {
            // 预览大图
            if (artwork.resultImageUrl) {
              const originalUrl = artwork.resultImageUrl.split('?')[0];
              wx.previewImage({
                current: originalUrl,
                urls: [originalUrl],
                showmenu: true
              });
            } else {
              wx.showToast({ title: '图片不存在', icon: 'none' });
            }
          }
        }
      });
    },
    
    // 保存原图到相册
    saveOriginalImage(url: string) {
      if (!url) {
        wx.showToast({ title: '图片不存在', icon: 'none' });
        return;
      }
      
      wx.showLoading({ title: '正在保存...' });
      
      // 下载图片到本地
      wx.downloadFile({
        url: url,
        success: (res) => {
          if (res.statusCode === 200) {
            // 保存图片到相册
            wx.saveImageToPhotosAlbum({
              filePath: res.tempFilePath,
              success: () => {
                wx.hideLoading();
                wx.showToast({ title: '保存成功', icon: 'success' });
              },
              fail: (err) => {
                wx.hideLoading();
                console.error('保存图片失败:', err);
                if (err.errMsg.indexOf('auth deny') !== -1) {
                  wx.showModal({
                    title: '提示',
                    content: '需要您授权保存图片到相册',
                    confirmText: '去授权',
                    cancelText: '取消',
                    success: (res) => {
                      if (res.confirm) {
                        wx.openSetting();
                      }
                    }
                  });
                } else {
                  wx.showToast({ title: '保存失败，请重试', icon: 'none' });
                }
              }
            });
          } else {
            wx.hideLoading();
            wx.showToast({ title: '图片下载失败', icon: 'none' });
          }
        },
        fail: () => {
          wx.hideLoading();
          wx.showToast({ title: '网络错误，请重试', icon: 'none' });
        }
      });
    },
    
    // 分割线滑动开始
    onSliderStart(e: any) {
      const id = e.currentTarget.dataset.id;
      this.setData({ currentSliderId: id });
      // 轻微振动反馈
      wx.vibrateShort({ type: 'light' });
    },
    
    // 分割线滑动中
    onSliderMove(e: any) {
      if (!this.data.currentSliderId) return;

      const touch = e.touches[0];
      const currentId = this.data.currentSliderId;

      console.log(`[SliderMove] ID: ${currentId}, Touch ClientX: ${touch.clientX}`);

      const query = wx.createSelectorQuery().in(this);
      // 使用 selectAll 获取所有 portfolio-item
      query.selectAll(`.portfolio-item`).boundingClientRect(rects => {
        if (!rects || !Array.isArray(rects)) {
           console.error(`[SliderMove] ID: ${currentId}, Failed to get boundingClientRect for .portfolio-item (selectAll)`);
           return;
        }

        // 在结果中查找当前 ID 对应的 rect
        const itemRect = rects.find(rect => rect.dataset && rect.dataset.id === currentId);

        if (!itemRect) {
          // 添加 data-id 到 WXML 的 portfolio-item 上，如果还没有的话
          console.error(`[SliderMove - SELECTALL] ID: ${currentId}, Failed to find rect for item with matching data-id.`);
          return;
        }

        console.log(`[SliderMove - SELECTALL] ID: ${currentId}, Item Rect:`, JSON.stringify(itemRect));

        const containerLeft = itemRect.left;
        const containerWidth = itemRect.width;

        if (containerWidth <= 0) {
           console.error(`[SliderMove - SELECTALL] ID: ${currentId}, Invalid item width: ${containerWidth}`);
           return;
        }

        const positionX = touch.clientX - containerLeft;
        let percent = (positionX / containerWidth) * 100;
        percent = Math.max(0, Math.min(100, percent));

        console.log(`[SliderMove - SELECTALL] ID: ${currentId}, Calculated PositionX: ${positionX}, Percent: ${percent}`);

        const sliderPositions = {...this.data.sliderPositions};
        sliderPositions[currentId] = percent;
        this.setData({ sliderPositions });

      }).exec();
    },
    
    // 分割线滑动结束
    onSliderEnd() {
      this.setData({ currentSliderId: null });
    },
    
    // 切换隐私状态
    togglePrivacy(e: any) {
      const id = e.currentTarget.dataset.id;
      const isPublic = e.currentTarget.dataset.isPublic;
      
      // 如果是设置为私密，直接调用
      if (isPublic) {
        this.updateArtworkStatus(id, false);
        return;
      }
      
      // 如果是设置为公开，显示选择对话框
      wx.showActionSheet({
        itemList: ['仅公开效果图', '公开效果图和原图'],
        itemColor: '#007aff',
        success: (res) => {
          if (res.tapIndex === 0) {
            // 仅公开效果图
            this.updateArtworkStatus(id, true, 'result_only');
          } else if (res.tapIndex === 1) {
            // 公开效果图和原图
            this.updateArtworkStatus(id, true, 'all');
          }
        }
      });
    },
    
    // 分享作品
    shareArtwork(e: any) {
      const id = e.currentTarget.dataset.id;
      const artwork = this.data.portfolio.find(item => item.id === id);
      if (!artwork) return;
      
      wx.vibrateShort({ type: 'light' });
      
      wx.showShareMenu({
        withShareTicket: true,
        menus: ['shareAppMessage', 'shareTimeline']
      });
      
      // 分享到微信
      wx.showActionSheet({
        itemList: ['分享给朋友', '分享到朋友圈'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 分享给朋友
            wx.showToast({ title: '请点击右上角分享', icon: 'none' });
          } else if (res.tapIndex === 1) {
            // 分享到朋友圈
            wx.showToast({ title: '请点击右上角分享到朋友圈', icon: 'none' });
          }
        }
      });
    },
    
    // 保存图片到相册
    saveImage(e: any) {
      const url = e.currentTarget.dataset.url;
      if (!url) {
        wx.showToast({ title: '图片不存在', icon: 'none' });
        return;
      }
      
      wx.vibrateShort({ type: 'light' });
      
      // 优先使用saveOriginalImage方法保存
      const originalUrl = url.split('?')[0];
      this.saveOriginalImage(originalUrl);
    },
    
    // 提示删除
    promptDelete(e: any) {
      const id = e.currentTarget.dataset.id;
      this.deleteArtwork(id);
    },
    
    // 长按操作
    onLongPress(e: any) {
      const id = e.currentTarget.dataset.id;
      const artwork = this.data.portfolio.find(item => item.id === id);
      if (!artwork) return;
      
      wx.vibrateShort({ type: 'medium' });
      
      const itemList: string[] = [];
      const itemActions: (() => void)[] = [];
      
      if (artwork.status === ArtworkStatus.Completed) {
        if (artwork.isPublic) {
          itemList.push('设为私密');
          itemActions.push(() => this.updateArtworkStatus(id, false));
        } else {
          itemList.push('公开 (仅效果图)');
          itemActions.push(() => this.updateArtworkStatus(id, true, 'result_only'));
          itemList.push('公开 (全部)');
          itemActions.push(() => this.updateArtworkStatus(id, true, 'all'));
        }
      }
      
      itemList.push('删除');
      itemActions.push(() => this.deleteArtwork(id));
      
      wx.showActionSheet({
        itemList: itemList,
        itemColor: '#007aff',
        success: (res) => {
          if (res.tapIndex >= 0 && itemActions[res.tapIndex]) {
            itemActions[res.tapIndex]();
          }
        }
      });
    },
    
    // 跳转到创作页
    goToCreate() {
      wx.vibrateShort({ type: 'light' });
      wx.switchTab({ url: '/pages/create/create' });
    },
    
    // 下拉刷新
    onPullDownRefresh() {
      if (!this.data.isLoading) {
        this.setData({ isRefreshing: true });
        this.loadPortfolio(true);
      } else {
        setTimeout(() => wx.stopPullDownRefresh(), 500);
      }
    }
  }
});