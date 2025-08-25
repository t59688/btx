// privacy.ts
Page({
  data: {},
  
  onLoad() {
    // 设置页面标题
    wx.setNavigationBarTitle({
      title: '用户协议与隐私政策'
    });
  },
  
  // 返回上一页
  goBack() {
    wx.navigateBack();
  }
}); 