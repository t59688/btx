/// <reference path="./types/index.d.ts" />

interface IAppOption {
  globalData: {
    userInfo?: WechatMiniprogram.UserInfo;
    regenerateImageUrl?: string; // 添加此字段用于存储重新生成的图片URL
  }
  userInfoReadyCallback?: WechatMiniprogram.GetUserInfoSuccessCallback,
} 