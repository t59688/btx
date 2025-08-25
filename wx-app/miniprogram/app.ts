// app.ts
import { autoLogin } from './utils/util';

App<IAppOption>({
  globalData: {},
  onLaunch() {
    // 展示本地存储能力
    const logs = wx.getStorageSync('logs') || []
    logs.unshift(Date.now())
    wx.setStorageSync('logs', logs)

    // 检查用户登录状态并自动登录
    const token = wx.getStorageSync('token')
    if (token) {
      // 有token，尝试验证并自动登录
      autoLogin().then((isLoggedIn) => {
        if (isLoggedIn) {
          // 登录成功，可以做一些初始化工作
          console.log('自动登录成功')
        } else {
          // 登录失败，autoLogin内部已经处理了跳转
          console.log('自动登录失败')
        }
      });
    } else {
      console.log('用户未登录')
      // 根据应用流程决定是否立即跳转到登录页
    }
  },
})