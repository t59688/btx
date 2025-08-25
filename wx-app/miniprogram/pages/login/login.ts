import { login, getUserInfo, request, uploadAvatar } from '../../utils/util';

Page({
  data: {
    avatarUrl: '',
    nickname: '',
    canLogin: false,
    avatarShape: 'square', // 新增头像形状控制：square 或 circle
    isLoading: false,  // 添加加载状态
    agreedToPolicy: false,  // 添加协议同意状态
    showPolicyTip: false  // 添加协议提示状态
  },

  onLoad() {
    // 检查是否已有用户信息
    const userInfo = getUserInfo();
    if (userInfo) {
      this.setData({
        avatarUrl: userInfo.avatar_url || '',
        nickname: userInfo.nickname || '',
        canLogin: this.checkCanLogin(userInfo.avatar_url, userInfo.nickname)
      });
    }
    
    // 添加多次检查，捕获微信自动填充
    this.checkNicknameField();
  },
  
  // 多次检查昵称字段
  checkNicknameField() {
    const checkTimes = [300, 600, 1000, 1500];
    
    checkTimes.forEach(time => {
      setTimeout(() => {
        // 获取DOM中的值
        const query = wx.createSelectorQuery();
        query.select('#nickname-input').fields({
          properties: ['value']
        }, res => {
          if (res && res.value && res.value.length > 0) {
            console.log('检测到输入框有值:', res.value);
            this.setData({
              nickname: res.value,
              canLogin: this.checkCanLogin(this.data.avatarUrl, res.value)
            });
          }
        }).exec();
      }, time);
    });
  },
  
  // 在页面显示时检查表单状态
  onShow() {
    setTimeout(() => {
      // 强制检查一次
      this.forceUpdateLoginStatus();
    }, 500);
  },
  
  // 强制更新登录状态
  forceUpdateLoginStatus() {
    // 获取当前表单状态
    const query = wx.createSelectorQuery();
    query.select('#nickname-input').fields({
      properties: ['value']
    }, res => {
      if (res && res.value) {
        const inputValue = res.value;
        console.log('强制检查输入框值:', inputValue);
        
        // 如果有值，强制启用登录按钮
        if (inputValue.trim().length > 0 && this.data.avatarUrl) {
          this.setData({
            nickname: inputValue,
            canLogin: true
          });
        }
      }
    }).exec();
  },

  // 微信头像选择事件回调
  onChooseAvatar(e: any) {
    const { avatarUrl } = e.detail;
    this.setData({
      avatarUrl,
      canLogin: this.checkCanLogin(avatarUrl, this.data.nickname)
    });
    
    // 显示上传中提示
    wx.showLoading({ title: '处理头像中...' });
    
    // 获取原始图片大小
    wx.getFileInfo({
      filePath: avatarUrl,
      success: (fileInfo) => {
        const originalSize = fileInfo.size;
        console.log(`原始头像大小: ${(originalSize / 1024).toFixed(2)}KB`);
        
        // 更新加载提示
        // wx.showLoading({ title: '处理中...' });
        
        // 压缩头像
        wx.compressImage({
          src: avatarUrl,
          quality: 10, // 高压缩率
          success: (compressRes) => {
            // 获取压缩后图片大小
            wx.getFileInfo({
              filePath: compressRes.tempFilePath,
              success: (compressedFileInfo) => {
                const compressedSize = compressedFileInfo.size;
                const compressionRatio = ((1 - compressedSize / originalSize) * 100).toFixed(2);
                
                console.log(`压缩后头像大小: ${(compressedSize / 1024).toFixed(2)}KB`);
                console.log(`压缩比例: ${compressionRatio}%`);
                
                // 更新加载提示
                wx.showLoading({ title: '上传头像中...' });
                
                // 上传压缩后的头像到服务器
                uploadAvatar(compressRes.tempFilePath).then(permanentUrl => {
                  console.log('头像已上传，永久链接:', permanentUrl);
                  // 更新头像URL为永久链接
                  this.setData({
                    avatarUrl: permanentUrl
                  });
                  wx.hideLoading();
                  
                  // 显示压缩结果提示
                  // wx.showToast({
                  //   title: `压缩成功: ${compressionRatio}%`,
                  //   icon: 'success',
                  //   duration: 2000
                  // });
                }).catch(err => {
                  console.error('头像上传失败:', err);
                  wx.hideLoading();
                  wx.showToast({
                    title: '头像上传失败',
                    icon: 'none'
                  });
                });
              },
              fail: (err) => {
                console.error('获取压缩后文件信息失败:', err);
                // 继续上传流程，忽略大小信息
                wx.showLoading({ title: '上传头像中...' });
                uploadAvatar(compressRes.tempFilePath).then(permanentUrl => {
                  this.setData({ avatarUrl: permanentUrl });
                  wx.hideLoading();
                }).catch(err => {
                  wx.hideLoading();
                  wx.showToast({ title: '头像上传失败', icon: 'none' });
                });
              }
            });
          },
          fail: (err) => {
            console.error('头像压缩失败:', err);
            wx.hideLoading();
            wx.showToast({
              title: '头像压缩失败',
              icon: 'none'
            });
          }
        });
      },
      fail: (err) => {
        console.error('获取原始文件信息失败:', err);
        // 继续压缩流程，忽略原始大小信息
        wx.compressImage({
          src: avatarUrl,
          quality: 10,
          success: (compressRes) => {
            uploadAvatar(compressRes.tempFilePath).then(permanentUrl => {
              this.setData({ avatarUrl: permanentUrl });
              wx.hideLoading();
            }).catch(err => {
              wx.hideLoading();
              wx.showToast({ title: '头像上传失败', icon: 'none' });
            });
          },
          fail: () => {
            wx.hideLoading();
            wx.showToast({ title: '头像压缩失败', icon: 'none' });
          }
        });
      }
    });
    
    // 头像更新后也强制检查一次
    setTimeout(() => this.forceUpdateLoginStatus(), 100);
  },

  // 昵称输入变化
  onNicknameChange(e: any) {
    const nickname = e.detail.value;
    this.setData({
      nickname,
      canLogin: this.checkCanLogin(this.data.avatarUrl, nickname)
    });
  },

  // 昵称自动填充后的检测
  onNicknameBlur(e: any) {
    const nickname = e.detail.value || '';
    console.log('输入框失焦，值为:', nickname);
    
    this.setData({
      nickname,
      canLogin: this.checkCanLogin(this.data.avatarUrl, nickname)
    });
    
    // 失焦后强制检查
    setTimeout(() => this.forceUpdateLoginStatus(), 100);
  },

  // 协议同意状态变化处理
  onPolicyAgreementChange(e: any) {
    const agreedToPolicy = e.detail.value.length > 0;
    this.setData({
      agreedToPolicy,
      // 如果同意协议，隐藏提示
      showPolicyTip: agreedToPolicy ? false : this.data.showPolicyTip
    });
  },

  // 显示协议提示
  showPolicyTip() {
    this.setData({ showPolicyTip: true });
    
    // 3秒后自动隐藏提示
    setTimeout(() => {
      this.setData({ showPolicyTip: false });
    }, 3000);
  },
  
  // 处理登录按钮点击
  handleLoginClick() {
    if (!this.data.canLogin || this.data.isLoading) {
      return;
    }
    
    if (!this.data.agreedToPolicy) {
      // 如果未勾选协议，显示提示
      this.showPolicyTip();
      // 提供触感反馈
      wx.vibrateShort({ type: 'light' });
      return;
    }
    
    // 执行登录
    this.login();
  },

  // 检查是否可以登录
  checkCanLogin(avatarUrl: string, nickname: string): boolean {
    const hasAvatar = !!avatarUrl;
    const hasNickname = !!nickname && nickname.trim().length > 0;
    
    console.log('检查登录条件:', hasAvatar, hasNickname);
    
    return hasAvatar && hasNickname;
  },

  // 登录
  login() {
    if (!this.data.canLogin || this.data.isLoading || !this.data.agreedToPolicy) return;

    // 设置加载状态
    this.setData({ isLoading: true });

    // 触感反馈
    wx.vibrateShort({ type: 'light' });

    // 显示加载提示
    wx.showLoading({ title: '登录中...' });

    // 获取登录code
    wx.login({
      success: async (loginRes) => {
        if (loginRes.code) {
          try {
            // 发送登录请求，包含code和用户信息
            // 此时avatarUrl应该已经是永久链接
            const loginRequest = {
              code: loginRes.code,
              user_info: {
                nickName: this.data.nickname,
                avatarUrl: this.data.avatarUrl
              }
            };
            
            // 发送到后端
            request('/auth/wechat/login', 'POST', loginRequest)
              .then((data) => {
                wx.hideLoading();
                // 存储token和用户信息
                wx.setStorageSync('token', data.access_token);
                wx.setStorageSync('user', data.user);
                
                // 清除登录导航标记
                wx.removeStorageSync('login_navigating');
                
                // 更新加载状态
                this.setData({ isLoading: false });
                
                // 提示登录成功
                wx.showToast({
                  title: '登录成功',
                  icon: 'success',
                  duration: 1500
                });
                
                // 在登录成功后，跳转前设置刷新标记
                setTimeout(() => {
                  // 检查是否有登录后需要跳转的页面
                  const redirectUrl = wx.getStorageSync('redirect_after_login');
                  
                  // 设置需要刷新gallery页面的标记
                  wx.setStorageSync('need_refresh_gallery', true);
                  
                  if (redirectUrl) {
                    // 清除存储的跳转URL
                    wx.removeStorageSync('redirect_after_login');
                    
                    // 判断是否是 tabBar 页面
                    const tabBarPages = ['/pages/gallery/gallery', '/pages/styles/styles', '/pages/create/create', '/pages/portfolio/portfolio'];
                    if (tabBarPages.some(page => redirectUrl.startsWith(page))) {
                      wx.switchTab({ url: redirectUrl });
                    } else {
                      wx.redirectTo({ url: redirectUrl });
                    }
                  } else {
                    // 如果没有重定向URL，则返回上一页或跳转首页
                    const pages = getCurrentPages();
                    if (pages.length > 1) {
                      wx.navigateBack();
                    } else {
                      wx.switchTab({
                        url: '/pages/gallery/gallery'
                      });
                    }
                  }
                }, 1500);
              })
              .catch((err) => {
                this.setData({ isLoading: false });
                wx.hideLoading();
                wx.showToast({
                  title: err.errMsg || '登录失败',
                  icon: 'none'
                });
              });
          } catch (error) {
            this.setData({ isLoading: false });
            wx.hideLoading();
            wx.showToast({
              title: '登录过程出现错误',
              icon: 'none'
            });
            console.error('登录错误:', error);
          }
        } else {
          this.setData({ isLoading: false });
          wx.hideLoading();
          wx.showToast({
            title: '获取微信登录凭证失败',
            icon: 'none'
          });
        }
      },
      fail: () => {
        this.setData({ isLoading: false });
        wx.hideLoading();
        wx.showToast({
          title: '微信登录授权失败',
          icon: 'none'
        });
      }
    });
  },

  // 跳过登录
  skipLogin() {
    // 触感反馈
    wx.vibrateShort({ type: 'light' });
    
    // 返回上一页或跳转到首页
    const pages = getCurrentPages();
    if (pages.length > 1) {
      wx.navigateBack();
    } else {
      wx.switchTab({
        url: '/pages/gallery/gallery'
      });
    }
  },

  // 查看隐私政策
  viewPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  },

  // 切换头像形状
  toggleAvatarShape() {
    // 在方形和圆形之间切换
    const newShape = this.data.avatarShape === 'square' ? 'circle' : 'square';
    this.setData({
      avatarShape: newShape
    });
    
    // 显示反馈
    wx.showToast({
      title: newShape === 'circle' ? '圆形头像' : '方形头像',
      icon: 'none',
      duration: 1000
    });
    
    // 触感反馈
    wx.vibrateShort({ type: 'light' });
  }
}); 