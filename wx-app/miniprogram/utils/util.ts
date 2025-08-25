export const formatTime = (date: Date) => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return (
    [year, month, day].map(formatNumber).join('/') +
    ' ' +
    [hour, minute, second].map(formatNumber).join(':')
  )
}

const formatNumber = (n: number) => {
  const s = n.toString()
  return s[1] ? s : '0' + s
}

// API基础URL
const BASE_URL = 'https://xx.xxx.com/api';
// const BASE_URL = 'http://localhost:8000/api';

// HTTP请求方法
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// 上传头像到服务器获取永久链接
export const uploadAvatar = (filePath: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${BASE_URL}/users/upload-avatar`,
      filePath,
      name: 'avatar',
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const data = JSON.parse(res.data);
          // 返回永久头像URL
          resolve(data.avatar_url);
        } else {
          reject({ errMsg: '上传头像失败', statusCode: res.statusCode });
        }
      },
      fail: (err) => {
        reject({ errMsg: '上传头像请求失败', error: err });
      }
    });
  });
};

// HTTP请求函数
export const request = (url: string, method: HttpMethod = 'GET', data?: any): Promise<any> => {
  return new Promise((resolve, reject) => {
    // 获取token
    const token = wx.getStorageSync('token');
    
    wx.request({
      url: `${BASE_URL}${url}`,
      method: method as | 'OPTIONS' | 'GET' | 'HEAD' | 'POST' | 'PUT' | 'DELETE' | 'TRACE' | 'CONNECT',
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        // @ts-ignore
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          // token失效或未授权
          // 清除本地存储的token和用户信息
          wx.removeStorageSync('token');
          wx.removeStorageSync('user');
          
          // 检查是否正在跳转到登录页
          const loginNavigating = wx.getStorageSync('login_navigating');
          const now = Date.now();
          
          // 如果没有跳转记录或者时间已经过去2秒以上
          if (!loginNavigating || (now - loginNavigating > 2000)) {
            // 设置跳转标记
            wx.setStorageSync('login_navigating', now);
            
            // 保存当前页面
            const pages = getCurrentPages();
            if (pages.length > 0) {
              const currentPage = pages[pages.length - 1];
              wx.setStorageSync('redirect_after_login', `/${currentPage.route}`);
            }
            
            // 显示提示
            wx.showToast({
              title: '登录已过期，请重新登录',
              icon: 'none',
              duration: 2000
            });
            
            // 延迟跳转到登录页
            setTimeout(() => {
              wx.navigateTo({
                url: '/pages/login/login',
                complete: () => {
                  // 导航完成后延迟重置标记
                  setTimeout(() => {
                    const currentMark = wx.getStorageSync('login_navigating');
                    if (currentMark === now) {
                      wx.removeStorageSync('login_navigating');
                    }
                  }, 2000);
                }
              });
            }, 1000);
          } else {
            console.log('已有登录页面跳转进行中，跳过401处理');
          }
          
          // 仍然reject，让调用方知道请求失败
          // @ts-ignore
          reject({ errMsg: (res.data && res.data.detail) || '登录已过期', statusCode: res.statusCode });
        } else {
          // 其他错误
          // @ts-ignore
          reject({ errMsg: (res.data && res.data.detail) || '请求失败', statusCode: res.statusCode });
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};

// 登录函数
export const login = (): Promise<{
  token: string;
  user: any;
}> => {
  return new Promise((resolve, reject) => {
    // 调用微信登录接口获取code
    wx.login({
      success: (res) => {
        if (res.code) {
          // 将code发送到后端进行登录
          request('/auth/wechat/login', 'POST', { code: res.code })
            .then((data) => {
              // 存储token
              wx.setStorageSync('token', data.access_token);
              // 存储用户信息
              wx.setStorageSync('user', data.user);
              resolve({
                token: data.access_token,
                user: data.user
              });
            })
            .catch((err) => {
              reject(err);
            });
        } else {
          reject({ errMsg: '微信登录失败' });
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};

// 获取用户信息并更新
export const getUserProfile = (): Promise<{
  token: string;
  user: any;
}> => {
  return new Promise((resolve, reject) => {
    // 获取用户信息
    wx.getUserProfile({
      desc: '用于完善会员资料',
      success: (userProfileRes) => {
        // 调用微信登录接口获取code
        wx.login({
          success: (loginRes) => {
            if (loginRes.code) {
              // 将code和用户信息发送到后端
              request('/auth/wechat/login', 'POST', { 
                code: loginRes.code,
                user_info: userProfileRes.userInfo
              })
                .then((data) => {
                  // 存储token
                  wx.setStorageSync('token', data.access_token);
                  // 存储用户信息
                  wx.setStorageSync('user', data.user);
                  resolve({
                    token: data.access_token,
                    user: data.user
                  });
                })
                .catch((err) => {
                  reject(err);
                });
            } else {
              reject({ errMsg: '微信登录失败' });
            }
          },
          fail: (err) => {
            reject(err);
          }
        });
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};

// 检查是否登录
export const checkLogin = (): boolean => {
  const isLoggedIn = !!wx.getStorageSync('token');
  
  // 如果已登录，直接返回
  if (isLoggedIn) return true;
  
  // 检查是否正在跳转
  const loginNavigating = wx.getStorageSync('login_navigating');
  const now = Date.now();
  
  // 如果有记录并且时间差小于2秒，说明刚刚已经开始跳转
  if (loginNavigating && (now - loginNavigating < 2000)) {
    console.log('已有登录页面跳转进行中，时间:', now - loginNavigating, 'ms');
    return false;
  }
  
  const currentPages = getCurrentPages();
  const currentPage = currentPages[currentPages.length - 1];
  const currentPageUrl = `/${currentPage.route}`;
  
  // 如果当前页面不是登录页，则记录当前页面并跳转到登录页
  if (currentPageUrl !== '/pages/login/login') {
    console.log('未登录，准备跳转到登录页');
    
    // 设置跳转标记和时间戳
    wx.setStorageSync('login_navigating', now);
    
    // 保存当前页面路径，登录后返回
    wx.setStorageSync('redirect_after_login', currentPageUrl);
    
    // 跳转到登录页
    wx.navigateTo({
      url: '/pages/login/login',
      complete: () => {
        // 跳转完成后，延迟移除标记
        setTimeout(() => {
          // 确保只删除当前设置的标记，避免删除其他进行中的跳转
          const currentMark = wx.getStorageSync('login_navigating');
          if (currentMark === now) {
            wx.removeStorageSync('login_navigating');
          }
        }, 2000);
      }
    });
  }
  
  return false;
};

// 获取用户信息
export const getUserInfo = (): any => {
  return wx.getStorageSync('user');
};

// 退出登录
export const logout = () => {
  wx.removeStorageSync('token');
  wx.removeStorageSync('user');
};

// 验证token是否有效并自动登录
export const autoLogin = (): Promise<boolean> => {
  return new Promise((resolve) => {
    // 检查是否有token
    const token = wx.getStorageSync('token');
    
    if (!token) {
      console.log('无token，需要登录');
      resolve(false);
      return;
    }
    
    // 发送请求验证token有效性
    // 可以请求一个需要登录的轻量级接口，例如获取用户信息
    request('/users/me', 'GET')
      .then(() => {
        // token有效
        console.log('token有效，已自动登录');
        resolve(true);
      })
      .catch((err) => {
        // token无效或请求失败
        // request函数会处理401错误并自动跳转到登录页
        console.log('token无效，需要重新登录', err);
        resolve(false);
      });
  });
};

// 检查页面是否需要登录
export const checkPageNeedsLogin = (pageUrl: string): boolean => {
  // 需要登录的页面列表 (已移除 gallery 和 styles 页面)
  const pagesNeedLogin = [
    '/pages/credits/credits',
    '/pages/portfolio/portfolio',
    '/pages/profile/profile',
    '/pages/create/create',
    // 添加其他需要登录的页面
  ];
  
  // 检查页面是否在需要登录的列表中
  return pagesNeedLogin.some(page => pageUrl.startsWith(page));
};

// 页面跳转拦截器
export const navigateWithLoginCheck = (options: {
  url: string,
  type?: 'navigateTo' | 'redirectTo' | 'switchTab' | 'reLaunch',
  success?: (res: any) => void,
  fail?: (res: any) => void,
  complete?: (res: any) => void
}) => {
  const { url, type = 'navigateTo', success, fail, complete } = options;
  
  // 检查页面是否需要登录
  if (checkPageNeedsLogin(url) && !wx.getStorageSync('token')) {
    // 检查是否正在跳转
    const loginNavigating = wx.getStorageSync('login_navigating');
    const now = Date.now();
    
    // 如果有记录并且时间差小于2秒，说明刚刚已经开始跳转
    if (loginNavigating && (now - loginNavigating < 2000)) {
      console.log('已有登录页面跳转进行中，跳过当前请求');
      if (typeof fail === 'function') {
        fail({ errMsg: '已有登录页面跳转进行中' });
      }
      return;
    }
    
    // 设置跳转标记
    wx.setStorageSync('login_navigating', now);
    
    // 需要登录但未登录，提示用户
    wx.showModal({
      title: '需要登录',
      content: '请先登录以访问此功能',
      confirmColor: '#007aff',
      success: (res) => {
        if (res.confirm) {
          // 保存用户想要访问的页面URL到本地存储
          // 登录成功后可以跳回此页面
          wx.setStorageSync('redirect_after_login', url);
          
          // 跳转到登录页
          wx.navigateTo({
            url: '/pages/login/login',
            success,
            fail,
            complete: (res) => {
              if (typeof complete === 'function') {
                complete(res);
              }
              // 延迟移除标记
              setTimeout(() => {
                // 确保只删除当前设置的标记
                const currentMark = wx.getStorageSync('login_navigating');
                if (currentMark === now) {
                  wx.removeStorageSync('login_navigating');
                }
              }, 2000);
            }
          });
        } else {
          // 用户取消登录
          if (typeof fail === 'function') {
            fail({ errMsg: '用户取消' });
          }
          // 立即移除跳转标记
          wx.removeStorageSync('login_navigating');
        }
      }
    });
    return;
  }
  
  // 不需要登录或已登录，正常跳转
  switch (type) {
    case 'navigateTo':
      wx.navigateTo({ url, success, fail, complete });
      break;
    case 'redirectTo':
      wx.redirectTo({ url, success, fail, complete });
      break;
    case 'switchTab':
      wx.switchTab({ url, success, fail, complete });
      break;
    case 'reLaunch':
      wx.reLaunch({ url, success, fail, complete });
      break;
  }
};
