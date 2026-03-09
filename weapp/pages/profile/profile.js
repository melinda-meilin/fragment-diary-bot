const api = require('../../utils/api');

Page({
  data: {
    nickname: '',
    avatarUrl: '',
    totalFragments: 0,
    totalDiaries: 0,
    streak: 0,
  },

  onShow() {
    const app = getApp();
    this.setData({
      nickname: app.globalData.nickname || '',
      avatarUrl: app.globalData.avatarUrl || '',
    });
    this.loadStats();
  },

  async loadStats() {
    try {
      // 用今日碎片数和日记历史来做简单统计
      const [fragments, diaries] = await Promise.all([
        api.getTodayFragments(),
        api.getDiaryHistory(365),
      ]);
      this.setData({
        totalFragments: fragments.count || 0,
        totalDiaries: (diaries.diaries || []).length,
        streak: this.calcStreak(diaries.diaries || []),
      });
    } catch (e) {
      console.error('Load stats failed:', e);
    }
  },

  /** 计算连续记录天数 */
  calcStreak(diaries) {
    if (!diaries.length) return 0;

    let streak = 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < diaries.length; i++) {
      const expected = new Date(today);
      expected.setDate(expected.getDate() - i);
      const expectedStr = expected.toISOString().slice(0, 10);

      if (diaries[i].diary_date === expectedStr) {
        streak++;
      } else {
        break;
      }
    }
    return streak;
  },
});
