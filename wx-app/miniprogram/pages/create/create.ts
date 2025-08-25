// create.ts
import { request } from '../../utils/util';

// 定义风格接口，与后端API响应匹配
interface Style {
  id: number;
  name: string;
  description: string | null;
  preview_url: string | null;
  category: string | null;
  category_id?: number;
  credits_cost: number;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  color?: string; // 前端使用的属性
  used_count?: number; // 前端使用的属性
}

// 移除旧的 IStyle 接口
// interface IStyle {
//   name: string;
//   cost: number;
//   previewUrl: string;
// }

interface IData {
  currentPoints: number;
  allStyles: Style[]; // 修改：用于存储从API获取的风格
  selectedStyle: Style | null; // 修改：类型改为 Style
  imageUploaded: boolean;
  imagePath: string | null;
  createButtonText: string;
  showCostOnButton: boolean;
  feedbackMessage: string;
  feedbackClass: string;
  isLoadingStyles: boolean; // 新增：加载状态
  isCompressingImage: boolean; // 新增：图片压缩状态
  isTaskSubmitted: boolean; // 新增：任务提交状态
}

// @ts-ignore
Page({
  data: {
    currentPoints: 0, // 修改：初始化为0
    allStyles: [], // 修改：初始化为空数组
    selectedStyle: null,
    imageUploaded: false,
    imagePath: null,
    createButtonText: '开始创作',
    showCostOnButton: false,
    feedbackMessage: '',
    feedbackClass: '',
    isLoadingStyles: false, // 新增：初始为false
    isCompressingImage: false, // 新增：初始为 false
    isTaskSubmitted: false, // 新增：初始为 false
  },

  // Lifecycle function - Called when page load
  onLoad() {
    // 检查是否有重新生成的图片URL
    // @ts-ignore
    const app = getApp();
    if (app.globalData && app.globalData.regenerateImageUrl) {
      // 有图片URL，自动加载此图片
      const imageUrl = app.globalData.regenerateImageUrl;
      
      this.setData({
        imagePath: imageUrl,
        imageUploaded: true,
        // 清除URL，避免重复使用
        feedbackMessage: '已自动加载原图',
        feedbackClass: 'success',
      });
      
      // 清除全局变量中的URL
      app.globalData.regenerateImageUrl = '';
    }
    
    // @ts-ignore
    this.loadUserCredits(); // 新增：加载用户积分
    // @ts-ignore
    this.loadStyles(); // 修改：调用加载风格的方法
    // @ts-ignore
    this.checkEnableCreateButton();
  },

  // 每次页面显示时刷新积分
  onShow() {
    // 检查是否有重新生成的图片URL
    // @ts-ignore
    const app = getApp();
    if (app.globalData && app.globalData.regenerateImageUrl) {
      // 有图片URL，自动加载此图片
      const imageUrl = app.globalData.regenerateImageUrl;
      console.log('从全局变量获取到图片URL:', imageUrl);
      
      this.setData({
        imagePath: imageUrl,
        imageUploaded: true,
        feedbackMessage: '已自动加载原图',
        feedbackClass: 'success',
      });
      
      // 清除全局变量中的URL
      app.globalData.regenerateImageUrl = '';
      
      // 检查按钮状态
      // @ts-ignore
      this.checkEnableCreateButton();
    }
    
    // @ts-ignore 忽略TypeScript检查
    this.loadUserCredits();
    
    // 每次显示页面时重置任务提交状态，让提示消失
    this.setData({
      isTaskSubmitted: false,
      // 不要清空feedbackMessage，因为我们可能刚刚设置了"已自动加载原图"
      // feedbackMessage: ''  // 清空提示消息
    });
  },

  // 新增：加载用户积分
  loadUserCredits() {
    request('/credits/balance', 'GET')
      .then(data => {
        if (data && data.balance !== undefined) {
          this.setData({
            currentPoints: data.balance
          });
          // @ts-ignore 忽略TypeScript检查
          this.checkEnableCreateButton(); // 重新检查按钮状态
        }
      })
      .catch(err => {
        console.error('获取积分余额失败:', err);
      });
  },

  // 新增：加载风格列表方法
  loadStyles() {
    this.setData({ isLoadingStyles: true });

    const params: any = {
      limit: 50, // 获取足够多的风格，暂不分页
      is_active: true, // 只显示活跃的风格
    };

    request(`/styles?${Object.keys(params).map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`).join('&')}`, 'GET')
      .then(data => {
        const styles: Style[] = data || [];
        // 对 preview_url 做一些处理，如果不存在，给一个默认值
        const formattedStyles = styles.map(style => ({
          ...style,
          preview_url: style.preview_url || `/images/styles/default_${style.name.toLowerCase().replace(/\s/g, '_')}.png` // 提供默认图
        }));
        this.setData({
          allStyles: formattedStyles,
        });
      })
      .catch(err => {
        console.error('加载风格失败:', err);
        wx.showToast({ title: '加载风格失败', icon: 'none' });
      })
      .finally(() => {
        this.setData({ isLoadingStyles: false });
      });
  },

  // Check button state and update feedback/button text
  checkEnableCreateButton() {
    const { imageUploaded, selectedStyle, currentPoints, isTaskSubmitted } = this.data;
    const requirementsMet = imageUploaded && !!selectedStyle;
    // 修改：使用 credits_cost
    const canAfford = selectedStyle ? currentPoints >= selectedStyle.credits_cost : false;

    let feedbackMsg = '';
    let feedbackCls = '';
    let showCost = false;

    if (requirementsMet && canAfford && !isTaskSubmitted) {
      showCost = true; // Show cost on button
    } else if (isTaskSubmitted) {
      feedbackMsg = '创建任务已提交';
      feedbackCls = 'success';
    } else {
      // 这里可以保留或修改提示逻辑
      // if (requirementsMet && !canAfford) {
      //   feedbackMsg = `积分不足 (需要 ${selectedStyle?.credits_cost})`;
      //   feedbackCls = 'error';
      // } else if (!imageUploaded && selectedStyle) {
      //   feedbackMsg = '请上传图片';
      // } else if (imageUploaded && !selectedStyle) {
      //   feedbackMsg = '请选择风格';
      // }
    }

    this.setData({
      showCostOnButton: showCost,
      // 修改：按钮文本显示 cost
      createButtonText: showCost && selectedStyle ? `开始创作` : '开始创作',
      feedbackMessage: feedbackMsg,
      feedbackClass: feedbackCls,
    });
  },

  // Handle image upload
  handleImageUpload() {
    // 重置任务提交状态
    this.setData({
      isTaskSubmitted: false
    });
    
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        if (res.tempFiles && res.tempFiles.length > 0) {
          const originalPath = res.tempFiles[0].tempFilePath;
          const originalSize = res.tempFiles[0].size; // 获取原始文件大小

          console.log(`原始图片路径: ${originalPath}, 大小: ${originalSize / 1024} KB`);

          // 开始压缩，显示加载提示
          this.setData({
            isCompressingImage: true,
            imagePath: originalPath, // 可以先显示原图预览
            imageUploaded: false, // 压缩完成前不算上传成功
            feedbackMessage: '',
            feedbackClass: '',
          });

          wx.compressImage({
            src: originalPath,
            quality: 25, // 按要求设置为 10
            success: (compressRes) => {
              const compressedPath = compressRes.tempFilePath;
              // 获取压缩后的大小（需要 wx.getFileInfo）
              wx.getFileInfo({
                filePath: compressedPath,
                success: (fileInfoRes) => {
                   console.log(`压缩后图片路径: ${compressedPath}, 大小: ${fileInfoRes.size / 1024} KB`);
                   // 更新页面数据，使用压缩后的路径
                   this.setData({
                     imagePath: compressedPath,
                     imageUploaded: true, // 标记图片已上传（压缩后）
                     isCompressingImage: false,
                   });
                   // @ts-ignore
                   this.checkEnableCreateButton(); // 检查按钮状态
                },
                fail: (fileInfoErr) => {
                  console.error("获取压缩后图片信息失败:", fileInfoErr);
                  // 即使获取信息失败，也尝试使用压缩路径
                  this.setData({
                    imagePath: compressedPath,
                    imageUploaded: true,
                    isCompressingImage: false,
                  });
                  // @ts-ignore
                  this.checkEnableCreateButton();
                }
              })
            },
            fail: (compressErr) => {
              console.error("图片压缩失败:", compressErr);
              wx.showToast({ title: '图片压缩失败', icon: 'none' });
              this.setData({
                isCompressingImage: false,
                imagePath: null, // 压缩失败，清除图片
                imageUploaded: false,
              });
              // @ts-ignore
              this.checkEnableCreateButton();
            }
          });
        }
      },
      fail: (err) => {
        // 仅在用户取消选择时提示，如果是其他错误则不提示
        if (err.errMsg !== 'chooseMedia:fail cancel') {
          console.error("选择图片失败:", err);
          wx.showToast({ title: '选择图片失败', icon: 'none' });
        }
      }
    });
  },

  // Handle style selection
  handleStyleSelect(event: WechatMiniprogram.TouchEvent) {
    // 重置任务提交状态
    this.setData({
      isTaskSubmitted: false
    });
    
    // 修改：event.currentTarget.dataset.style 现在是完整的 Style 对象
    const selected: Style = event.currentTarget.dataset.style;
    this.setData({
      selectedStyle: selected,
      feedbackMessage: '', // Clear feedback on new selection
      feedbackClass: '',
    });
    // @ts-ignore
    this.checkEnableCreateButton();
  },

  // Handle create button click
  handleCreateClick() {
    const { imageUploaded, selectedStyle, currentPoints, imagePath } = this.data;

    // 前置检查
    if (!imageUploaded || !selectedStyle || !imagePath) {
      wx.showToast({ title: '请先上传图片并选择风格', icon: 'none' });
      return;
    }

    // 再次检查积分（虽然按钮已禁用，但作为双重保险）
    if (currentPoints < selectedStyle.credits_cost) {
      wx.showToast({ title: `积分不足 (需要 ${selectedStyle.credits_cost})`, icon: 'none' });
      return;
    }

    this.setData({
      feedbackMessage: `正在提交创作请求...`,
      feedbackClass: 'processing',
    });
    wx.showLoading({ title: '正在创建...', mask: true });

    // 检查imagePath是否为URL或者本地文件路径
    const isImageUrl = (imagePath.startsWith('http://') || imagePath.startsWith('https://')) && !imagePath.startsWith('http://tmp/');

    // 创建通用的API请求处理函数
    const submitRequest = (requestData: any) => {
      request('/artworks', 'POST', requestData)
        .then((artworkRes: any) => {
          wx.hideLoading();
          // 更新任务提交状态
          this.setData({
            feedbackMessage: '创建任务已提交',
            feedbackClass: 'success',
            isTaskSubmitted: true,
            // 可选：清空当前页面的选择，避免重复提交
            imagePath: null,
            imageUploaded: false,
            selectedStyle: null,
            createButtonText: '开始创作',
            showCostOnButton: false,
          });
          
          // 刷新积分余额
          // @ts-ignore 忽略TypeScript检查
          this.loadUserCredits();

          // 显示短暂成功提示
          wx.showToast({ title: '创建成功！', icon: 'success', duration: 1500 });

          // 4. 跳转到作品集页面
          setTimeout(() => {
            wx.switchTab({
              url: '/pages/portfolio/portfolio'
            });
          }, 1500);
        })
        .catch((err) => {
          wx.hideLoading();
          console.error('创建作品失败:', err);
          let errMsg = '创建作品失败，请稍后再试';
          // 尝试从后端返回获取错误信息
          if (err && err.data && err.data.detail) {
            errMsg = err.data.detail;
          } else if (err && err.statusCode === 401) {
            errMsg = '请先登录'; // 或者跳转到登录页
          } else if (err && err.statusCode === 422) {
            errMsg = '请求参数错误';
          }
          
          this.setData({
            feedbackMessage: errMsg,
            feedbackClass: 'error',
            isTaskSubmitted: false,
          });
          wx.showToast({ title: errMsg, icon: 'none', duration: 2000 });
        });
    };

    if (isImageUrl) {
      // 直接使用URL创建艺术作品
      const requestData = {
        style_id: selectedStyle.id,
        image_url: imagePath,
      };
      console.log('直接使用URL创建艺术作品:', requestData);
      // 调用创建作品API
      submitRequest(requestData);
    } else {
      // 使用本地文件，需要转换为Base64
      // 1. 读取图片文件并转换为 Base64
      const fs = wx.getFileSystemManager();
      fs.readFile({
        filePath: imagePath,
        encoding: 'base64',
        success: (res) => {
          // @ts-ignore
          const base64Data = res.data;
          // 尝试从文件路径或类型推断前缀，如果压缩后固定为jpg则可以直接用
          // 注意：wx.compressImage 在 iOS 上只输出 jpg，安卓上可能保持原格式
          // 简单起见，我们先假设是 jpeg，如果后端需要更精确的类型，需要进一步判断
          const imageBase64 = `data:image/jpeg;base64,${base64Data}`;

          // 2. 构造请求体
          const requestData = {
            style_id: selectedStyle.id,
            image_base64: imageBase64,
          };

          // 3. 调用创建作品API
          console.log('使用本地文件创建艺术作品:', requestData);
          submitRequest(requestData);
        },
        fail: (err) => {
          wx.hideLoading();
          console.error("读取图片文件失败:", err);
          this.setData({
            feedbackMessage: '图片处理失败，请重试',
            feedbackClass: 'error',
            isTaskSubmitted: false,
          });
          wx.showToast({ title: '图片处理失败', icon: 'none' });
        }
      });
    }
  },
} as WechatMiniprogram.Page.Options<IData, WechatMiniprogram.Page.Instance<IData, object>>);

