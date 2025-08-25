// styles.ts
import { request } from '../../utils/util';

export {};
const app = getApp<IAppOption>();

// 定义分类接口
interface Category {
  id: string;
  name: string;
  color?: string;
}

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

Component({
  data: {
    currentCategory: 'all',
    categories: [
      { id: 'all', name: '全部' }
    ] as Category[],
    styles: [] as Style[],
    isLoading: false,
    skip: 0,
    limit: 12, // 调整限制数量
    noMoreData: false,
    isRefreshing: false,
    searchQuery: '',
  },
  
  lifetimes: {
    attached() {
      this.loadCategories();
      this.loadStyles(true);
    }
  },
  
  methods: {
    // 加载分类
    loadCategories() {
      this.setData({ isLoading: true });
      
      request('/categories', 'GET')
        .then(data => {
          const categories: Category[] = [{ id: 'all', name: '全部' }];
          
          if (data && Array.isArray(data)) {
            data.forEach((category: any) => {
              categories.push({
                id: category.id.toString(),
                name: category.name,
                color: category.color
              });
            });
          }
          
          this.setData({ categories });
        })
        .catch(err => {
          console.error('加载分类失败:', err);
          wx.showToast({ title: '加载分类失败', icon: 'none' });
        })
        .finally(() => {
          this.setData({ isLoading: false });
        });
    },
    
    // 切换分类
    switchCategory(e: any) {
      const categoryId = e.currentTarget.dataset.id;
      if (this.data.currentCategory !== categoryId) {
        // 触感反馈
        wx.vibrateShort({ type: 'light' });
        
        this.setData({
          currentCategory: categoryId,
          styles: [], // 清空当前样式列表，避免显示旧内容
          skip: 0,
          isLoading: true,
          noMoreData: false,
          searchQuery: '',
        });
        this.loadStyles(true);
      }
    },
    
    // 加载风格列表
    loadStyles(refresh = false) {
      if (this.data.isLoading && !refresh) return;
      if (!refresh && this.data.noMoreData) return;
      
      this.setData({ isLoading: true });
      
      if (refresh) {
        this.setData({ skip: 0, noMoreData: false, styles: [] });
      }
      
      const params: any = {
        skip: this.data.skip,
        limit: this.data.limit,
        is_active: true, // 只显示活跃的风格
        search: this.data.searchQuery || undefined, // 搜索条件
      };
      
      // 如果分类不是"全部"，则添加分类筛选
      if (this.data.currentCategory !== 'all') {
        params.category_id = this.data.currentCategory;
      }
      
      // 移除未定义的参数
      Object.keys(params).forEach(key => params[key] === undefined && delete params[key]);
      const queryString = Object.keys(params)
          .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
          .join('&');

      request(`/styles?${queryString}`, 'GET')
        .then(data => {
          const newStyles = data || [];
          const noMore = newStyles.length < this.data.limit;
          
          // 格式化风格数据
          const formattedStyles = newStyles.map((item: Style) => {
            let categoryColor = '#8e8e93'; // 默认颜色
            
            // 获取风格对应的颜色
            if (item.category) {
              categoryColor = this.getStyleColor(item.category);
            }
            
            return {
              id: item.id,
              name: item.name,
              color: item.color || categoryColor,
              previewUrl: item.preview_url || this.getDefaultPreviewUrl(item.name),
              usedCount: item.used_count || 0,
              category: item.category,
              categoryId: item.category_id,
              credits_cost: item.credits_cost
            };
          });
          
          this.setData({
            styles: refresh ? formattedStyles : [...this.data.styles, ...formattedStyles],
            skip: this.data.skip + newStyles.length,
            noMoreData: noMore,
            isLoading: false,
            isRefreshing: false,
          });
        })
        .catch(err => {
          console.error('加载风格失败:', err);
          wx.showToast({ title: '加载失败，请稍后重试', icon: 'none' });
          this.setData({ isLoading: false, isRefreshing: false });
        });
    },
    
    // 获取风格对应的颜色
    getStyleColor(category: string): string {
      const styleColors: Record<string, string> = {
        'classic': '#3b3a39',
        'modern': '#2c7873',
        'cyberpunk': '#7209b7',
        'anime': '#3a86ff',
        'chinese': '#f72585',
        'abstract': '#ff9500'
      };
      
      return styleColors[category] || '#8e8e93';
    },
    
    // 获取默认预览图URL（如果API没有返回）
    getDefaultPreviewUrl(styleName: string): string {
      // 可以根据风格名称返回默认图片路径
      return `/images/styles/default_${styleName.toLowerCase().replace(/\s/g, '_')}.png`;
    },
    
    // 选择风格
    selectStyle(e: any) {
      const styleId = e.currentTarget.dataset.id;
      const style = this.data.styles.find(item => item.id === styleId);
      
      if (style) {
        // 触感反馈
        wx.vibrateShort({ type: 'light' });
        
        // 如果是长按则预览图片（采用冒泡方式处理点击事件）
        if (e.type === 'longpress') {
          this.previewStyleImage(style);
          return;
        }
        
        // 查找选中的风格详情（如果需要在前一页使用）
        const pages = getCurrentPages();
        const prevPage = pages[pages.length - 2]; // 获取前一页实例
        if (prevPage && prevPage.route === 'pages/create/create') { // 检查前一页是否是创作页
           prevPage.setData({
              selectedStyleId: style.id,
              selectedStyleName: style.name,
              selectedStyleColor: style.color
           });
           wx.navigateBack(); // 返回创作页
        } else {
            // 如果不是从创作页来，可以预览风格图片
            this.previewStyleImage(style);
        }
      }
    },
    
    // 预览风格图片
    previewStyleImage(style: any) {
      if (style && style.previewUrl) {
        wx.previewImage({
          current: style.previewUrl,
          urls: [style.previewUrl],
          showmenu: true
        });
      } else {
        wx.showToast({ title: '风格预览图不存在', icon: 'none' });
      }
    },
    
    // 搜索输入事件
    onSearchInput(e: any) {
      this.setData({ searchQuery: e.detail.value });
    },
    
    // 搜索确认事件
    onSearchConfirm() {
      // 重新加载风格列表，应用搜索条件
      this.setData({ skip: 0, noMoreData: false, styles: [] });
      this.loadStyles(true);
    },
    
    // 清除搜索
    clearSearch() {
      this.setData({ searchQuery: '' });
      // 如果之前有搜索条件，则重新加载
      if (this.data.searchQuery) {
        this.loadStyles(true);
      }
    },
    
    // 加载更多
    loadMoreStyles() {
      this.loadStyles(false);
    },
    
    // 下拉刷新
    onPullDownRefresh() {
      if (!this.data.isLoading) {
        this.setData({ isRefreshing: true });
        this.loadStyles(true);
      } else {
        setTimeout(() => wx.stopPullDownRefresh(), 500);
      }
    }
  }
}) 