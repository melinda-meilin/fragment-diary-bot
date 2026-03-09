const api = require('../../utils/api');

Page({
  data: {
    diaries: [],
  },

  onShow() {
    this.loadDiaries();
  },

  async loadDiaries() {
    try {
      const res = await api.getDiaryHistory(30);
      const diaries = (res.diaries || []).map(d => ({
        ...d,
        preview: (d.content || '').replace(/[#*>\-]/g, '').slice(0, 120),
      }));
      this.setData({ diaries });
    } catch (e) {
      console.error('Load diaries failed:', e);
    }
  },

  /** 手动生成日记 */
  async onGenerate() {
    wx.showLoading({ title: '正在撰写日记...' });
    try {
      await api.generateDiary();
      wx.hideLoading();
      wx.showToast({ title: '日记已生成', icon: 'success' });
      this.loadDiaries();
    } catch (e) {
      wx.hideLoading();
      const msg = (e && e.detail) || '生成失败，可能今天还没有碎片';
      wx.showToast({ title: msg, icon: 'none' });
    }
  },

  /** 点击查看详情 */
  onTapDiary(e) {
    const date = e.currentTarget.dataset.date;
    wx.navigateTo({ url: `/pages/diary-detail/diary-detail?date=${date}` });
  },
});
