import { request, checkLogin, logout } from '../../utils/util';

export {};
const app = getApp<IAppOption>();

Component({
  data: {
    sortType: 'latest', // 默认排序方式
    artworks: [] as any[],
    skip: 0,
    limit: 12, // 每页加载数量
    isLoading: false,
    noMoreData: false,
    isRefreshing: false,
    currentSliderId: null as string | null, // 当前正在滑动的分割线ID
  },
  
  lifetimes: {
    attached() {
      this.loadArtworks(true);
    }
  },
  
  methods: {
    // 设置排序方式
    setSortType(e: any) {
      const type = e.currentTarget.dataset.type;
      if (this.data.sortType !== type) {
        // 触感反馈
        wx.vibrateShort({ type: 'light' });
        
        this.setData({
          sortType: type,
          artworks: [],
          skip: 0,
          noMoreData: false
        });
        
        this.loadArtworks(true);
      }
    },
    
    // 加载画廊作品
    loadArtworks(refresh = false) {
      if (this.data.isLoading) return;
      if (!refresh && this.data.noMoreData) return;
      
      this.setData({ isLoading: true });
      
      if (refresh) {
        this.setData({ skip: 0, noMoreData: false, artworks: [] });
      }
      
      // 构建API请求参数
      const params: any = {
        skip: this.data.skip,
        limit: this.data.limit,
        is_public: true // 只显示公开作品
      };
      
      // 根据排序类型设置排序参数
      let orderBy = 'created_at'; // 默认按创建时间排序
      
      if (this.data.sortType === 'popular') {
        orderBy = 'views_count'; // 按浏览量排序
      } else if (this.data.sortType === 'likes') {
        orderBy = 'likes_count'; // 按点赞数排序
      }
      
      params.order_by = orderBy;
      params.order_desc = true; // 降序排列
      
      // 生成查询字符串
      const queryString = Object.keys(params)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
        .join('&');
      
      // 调用API获取画廊数据
      request(`/artworks/gallery?${queryString}`, 'GET')
        .then(data => {
          const artworks = data || [];
          const noMore = artworks.length < this.data.limit;
          
          // 格式化作品数据
          const formattedArtworks = artworks.map((item: any) => ({
            id: item.id,
            result_image_url: item.result_image_url ? `${item.result_image_url}?imageMogr2/thumbnail/!40p` : '',
            source_image_url: item.source_image_url || '',
            style_name: item.style_name || '未知风格',
            user: item.user || null,
            likes_count: item.likes_count || 0,
            isLiked: item.is_liked_by_current_user || false,
            views_count: item.views_count || 0,
            formattedCreateTime: this.formatDate(item.created_at),
            sliderPosition: 50 // 设置默认滑块位置为50%
          }));
          
          this.setData({
            artworks: refresh ? formattedArtworks : [...this.data.artworks, ...formattedArtworks],
            skip: this.data.skip + artworks.length,
            noMoreData: noMore,
            isLoading: false,
            isRefreshing: false,
          });
        })
        .catch(err => {
          console.error('加载画廊数据失败:', err);
          wx.showToast({ title: '加载失败，请稍后重试', icon: 'none' });
          this.setData({ isLoading: false, isRefreshing: false });
        });
    },
    
    // 查看作品详情
    viewArtworkDetail(e: any) {
      const id = e.currentTarget.dataset.id;
      wx.vibrateShort({ type: 'light' });
      
      // 找到要预览的作品
      const artwork = this.data.artworks.find(item => item.id === id);
      if (artwork && artwork.result_image_url) {
        wx.previewImage({
          current: artwork.result_image_url, // 当前显示图片的链接
          urls: [artwork.result_image_url], // 需要预览的图片链接列表
          showmenu: true // 显示长按菜单
        });
        
        // 异步增加浏览量（可选）
        this.increaseViewCount(id);
      } else {
        wx.showToast({ title: '图片不存在', icon: 'none' });
      }
    },
    
    // 处理长按作品事件
    handleLongPressArtwork(e: any) {
      const id = e.currentTarget.dataset.id;
      wx.vibrateShort({ type: 'medium' });
      
      // 找到要操作的作品
      const artwork = this.data.artworks.find(item => item.id === id);
      if (artwork && artwork.result_image_url) {
        // 获取原始图片URL（去除可能的缩略图参数）
        const originalUrl = artwork.result_image_url.split('?')[0];
        
        wx.showActionSheet({
          itemList: [ '预览','保存原图到相册'],
          success: (res) => {
            if (res.tapIndex === 0) {
              // 保存原图到相册
              this.saveImageToAlbum(originalUrl);
            } else if (res.tapIndex === 1) {
              // 预览大图
              wx.previewImage({
                current: originalUrl,
                urls: [originalUrl],
                showmenu: true
              });
              // 异步增加浏览量
              this.increaseViewCount(id);
            }
          }
        });
      } else {
        wx.showToast({ title: '图片不存在', icon: 'none' });
      }
    },
    
    // 保存图片到相册
    saveImageToAlbum(url: string) {
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
    
    // 增加浏览量的方法（可选）
    increaseViewCount(id: string) {
      request(`/artworks/${id}/view`, 'POST')
        .catch(err => {
          console.error('增加浏览量失败:', err);
        });
    },
    
    // 点赞/取消点赞作品
    toggleLike(event: WechatMiniprogram.TouchEvent) {
      // 检查登录状态
      const isLoggedIn = !!wx.getStorageSync('token');
      if (!isLoggedIn) {
        // 提示用户登录
        wx.showModal({
          title: '需要登录',
          content: '登录后才能点赞作品',
          confirmText: '去登录',
          cancelText: '取消',
          confirmColor: '#007aff',
          success: (res) => {
            if (res.confirm) {
              // 用户点击"去登录"，跳转到登录页面
              wx.navigateTo({
                url: '/pages/login/login'
              });
            }
          }
        });
        return;
      }
      
      const { id, index } = event.currentTarget.dataset;
      if (typeof index !== 'number' || !this.data.artworks[index]) {
        console.error("无效的作品索引或ID:", index, id);
        return;
      }

      const artwork = this.data.artworks[index];
      const originalIsLiked = artwork.isLiked;
      const originalLikesCount = artwork.likes_count || 0;
      const newIsLiked = !originalIsLiked;
      const newLikesCount = newIsLiked ? originalLikesCount + 1 : originalLikesCount - 1;
      
      // 触感反馈
      wx.vibrateShort({ type: 'light' });
      
      // 1. 乐观更新 UI
      this.setData({
        [`artworks[${index}].isLiked`]: newIsLiked,
        [`artworks[${index}].likes_count`]: newLikesCount < 0 ? 0 : newLikesCount, // 保证点赞数不为负
      });
      
      // 2. 调用 API 更新后端数据
      // 假设点赞用 POST /likes/{id}，取消点赞用 DELETE /likes/{id}
      const apiUrl = `/likes/${id}`;
      const method = newIsLiked ? 'POST' : 'DELETE';
      
      request(apiUrl, method)
        .then(responseData => {
          // 3. 请求成功
          console.log('点赞/取消点赞 成功:', responseData);
          // 可以选择性地用服务器返回的最新点赞数更新界面，以防万一
          if (responseData && typeof responseData.likes_count === 'number' && responseData.likes_count !== newLikesCount) {
             console.log('与服务器点赞数同步:', responseData.likes_count);
             this.setData({ [`artworks[${index}].likes_count`]: responseData.likes_count });
          }
          // 乐观更新已完成，通常无需其他操作
        })
        .catch(err => {
          // 4. 请求失败，回滚 UI
          console.error('点赞/取消点赞 失败:', err);
          wx.showToast({ title: '操作失败，请重试', icon: 'none' });
          
          // 恢复到操作前的状态
          this.setData({
            [`artworks[${index}].isLiked`]: originalIsLiked,
            [`artworks[${index}].likes_count`]: originalLikesCount,
          });
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
      
      // 找到当前作品的索引
      const artworkIndex = this.data.artworks.findIndex(item => item.id === currentId);
      if (artworkIndex === -1) return;

      const query = wx.createSelectorQuery().in(this);
      query.selectAll('.gallery-item').boundingClientRect(rects => {
        if (!rects || !Array.isArray(rects) || artworkIndex >= rects.length) {
          console.error('获取元素位置失败');
          return;
        }

        const itemRect = rects[artworkIndex];
        const containerLeft = itemRect.left;
        const containerWidth = itemRect.width;

        if (containerWidth <= 0) {
          console.error('无效的容器宽度');
          return;
        }

        const positionX = touch.clientX - containerLeft;
        let percent = (positionX / containerWidth) * 100;
        percent = Math.max(0, Math.min(100, percent));

        this.setData({
          [`artworks[${artworkIndex}].sliderPosition`]: percent
        });
      }).exec();
    },
    
    // 分割线滑动结束
    onSliderEnd() {
      this.setData({ currentSliderId: null });
    },
    
    // 加载更多作品
    loadMoreArtworks() {
      this.loadArtworks(false);
    },
    
    // 下拉刷新
    onPullDownRefresh() {
      if (!this.data.isLoading) {
        this.setData({ isRefreshing: true });
        this.loadArtworks(true);
      } else {
        setTimeout(() => wx.stopPullDownRefresh(), 500);
      }
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

    onShow() {
      // 检查是否需要刷新数据
      const needRefresh = wx.getStorageSync('need_refresh_gallery');
      if (needRefresh) {
        // 清除刷新标记
        wx.removeStorageSync('need_refresh_gallery');
        
        // 刷新页面数据
        this.loadArtworks(true);
      }
    }
  }
})
