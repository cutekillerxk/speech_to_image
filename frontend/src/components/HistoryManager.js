/**
 * 历史记录管理器
 * 使用localStorage存储生成的历史记录
 */

const STORAGE_KEY = 'audioToImageHistory';
const MAX_HISTORY = 50; // 最多保存50条记录

class HistoryManager {
  /**
   * 加载历史记录
   */
  static loadHistory() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (data) {
        return JSON.parse(data);
      }
    } catch (error) {
      console.error('加载历史记录失败:', error);
    }
    return [];
  }

  /**
   * 保存历史记录
   */
  static saveHistory(history) {
    try {
      // 限制历史记录数量
      const limitedHistory = history.slice(-MAX_HISTORY);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(limitedHistory));
    } catch (error) {
      console.error('保存历史记录失败:', error);
      // 如果存储空间不足，尝试删除旧记录
      if (error.name === 'QuotaExceededError') {
        const limitedHistory = history.slice(-Math.floor(MAX_HISTORY / 2));
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(limitedHistory));
        } catch (e) {
          console.error('清理后仍无法保存:', e);
        }
      }
    }
  }

  /**
   * 清空历史记录
   */
  static clearHistory() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('清空历史记录失败:', error);
    }
  }

  /**
   * 删除单条记录
   */
  static deleteItem(id) {
    const history = this.loadHistory();
    const filtered = history.filter(item => item.id !== id);
    this.saveHistory(filtered);
    return filtered;
  }
}

export default HistoryManager;

