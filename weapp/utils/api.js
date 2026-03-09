/**
 * API 请求封装 — 自动带 token
 */
const app = getApp();

function request(options) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.baseUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        Authorization: `Bearer ${app.globalData.token}`,
        'Content-Type': options.contentType || 'application/json',
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail: reject,
    });
  });
}

/** 发送文字碎片 */
function sendTextFragment(content) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.baseUrl}/fragments/text`,
      method: 'POST',
      header: {
        Authorization: `Bearer ${app.globalData.token}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      data: { content },
      success(res) { resolve(res.data); },
      fail: reject,
    });
  });
}

/** 上传照片碎片 */
function sendPhotoFragment(filePath, caption) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${app.globalData.baseUrl}/fragments/photo`,
      filePath,
      name: 'file',
      formData: { caption: caption || '' },
      header: { Authorization: `Bearer ${app.globalData.token}` },
      success(res) { resolve(JSON.parse(res.data)); },
      fail: reject,
    });
  });
}

/** 上传语音碎片 */
function sendVoiceFragment(filePath) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${app.globalData.baseUrl}/fragments/voice`,
      filePath,
      name: 'file',
      header: { Authorization: `Bearer ${app.globalData.token}` },
      success(res) { resolve(JSON.parse(res.data)); },
      fail: reject,
    });
  });
}

/** 获取今日碎片 */
function getTodayFragments() {
  return request({ url: '/fragments/today' });
}

/** 获取日记列表 */
function getDiaryHistory(days = 30) {
  return request({ url: `/diaries/history?days=${days}` });
}

/** 获取某天日记 */
function getDiary(date) {
  return request({ url: `/diaries/${date}` });
}

/** 手动生成日记 */
function generateDiary(date) {
  return request({ url: '/diaries/generate', method: 'POST', data: { target_date: date } });
}

module.exports = {
  request,
  sendTextFragment,
  sendPhotoFragment,
  sendVoiceFragment,
  getTodayFragments,
  getDiaryHistory,
  getDiary,
  generateDiary,
};
