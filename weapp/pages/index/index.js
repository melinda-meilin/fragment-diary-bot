const api = require('../../utils/api');

Page({
  data: {
    today: '',
    fragments: [],
    inputText: '',
    isRecording: false,
  },

  onLoad() {
    const now = new Date();
    this.setData({
      today: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`,
    });
  },

  onShow() {
    this.loadFragments();
  },

  /** 加载今日碎片 */
  async loadFragments() {
    try {
      const res = await api.getTodayFragments();
      const fragments = (res.fragments || []).map(f => ({
        ...f,
        timeStr: f.created_at ? f.created_at.slice(11, 16) : '',
      }));
      this.setData({ fragments });
    } catch (e) {
      console.error('Load fragments failed:', e);
    }
  },

  /** 输入框 */
  onInput(e) {
    this.setData({ inputText: e.detail.value });
  },

  /** 发送文字碎片 */
  async onSendText() {
    const content = this.data.inputText.trim();
    if (!content) return;

    this.setData({ inputText: '' });

    try {
      await api.sendTextFragment(content);
      wx.showToast({ title: '已记录 ✓', icon: 'success' });
      this.loadFragments();
    } catch (e) {
      wx.showToast({ title: '记录失败', icon: 'error' });
    }
  },

  /** 选择照片 */
  onChoosePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: async (res) => {
        const file = res.tempFiles[0];
        wx.showLoading({ title: '上传中...' });
        try {
          await api.sendPhotoFragment(file.tempFilePath);
          wx.hideLoading();
          wx.showToast({ title: '已记录 ✓', icon: 'success' });
          this.loadFragments();
        } catch (e) {
          wx.hideLoading();
          wx.showToast({ title: '上传失败', icon: 'error' });
        }
      },
    });
  },

  /** 开始录音 */
  onStartRecord() {
    this.setData({ isRecording: true });

    const recorderManager = wx.getRecorderManager();
    recorderManager.onStop((res) => {
      this.setData({ isRecording: false });
      if (res.duration < 1000) {
        wx.showToast({ title: '录音太短', icon: 'none' });
        return;
      }
      this.uploadVoice(res.tempFilePath);
    });

    recorderManager.start({
      duration: 60000,        // 最长 60 秒
      sampleRate: 16000,
      numberOfChannels: 1,
      format: 'mp3',
    });
  },

  /** 停止录音 */
  onStopRecord() {
    if (this.data.isRecording) {
      wx.getRecorderManager().stop();
    }
  },

  /** 上传语音 */
  async uploadVoice(filePath) {
    wx.showLoading({ title: '上传中...' });
    try {
      await api.sendVoiceFragment(filePath);
      wx.hideLoading();
      wx.showToast({ title: '已记录 ✓', icon: 'success' });
      this.loadFragments();
    } catch (e) {
      wx.hideLoading();
      wx.showToast({ title: '上传失败', icon: 'error' });
    }
  },
});
