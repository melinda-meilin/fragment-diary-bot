/**
 * 碎片日记 — 小程序入口
 */
App({
  globalData: {
    token: '',
    openid: '',
    baseUrl: 'https://fragment-diary-bot.onrender.com/api', // ← 替换成你的后端地址
  },

  onLaunch() {
    this.login();
  },

  /** 微信登录 → 后端换 token */
  login() {
    const that = this;
    wx.login({
      success(res) {
        if (!res.code) return;

        wx.request({
          url: `${that.globalData.baseUrl}/auth/login`,
          method: 'POST',
          data: { code: res.code },
          success(resp) {
            if (resp.data.token) {
              that.globalData.token = resp.data.token;
              that.globalData.openid = resp.data.openid;
              console.log('Login success');
            }
          },
          fail(err) {
            console.error('Login failed:', err);
          },
        });
      },
    });
  },
});
