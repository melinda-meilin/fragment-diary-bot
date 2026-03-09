const api = require('../../utils/api');

Page({
  data: {
    date: '',
    contentHtml: '',
    fragmentCount: 0,
  },

  async onLoad(options) {
    const date = options.date;
    this.setData({ date });

    try {
      const diary = await api.getDiary(date);
      this.setData({
        contentHtml: this.markdownToHtml(diary.content),
        fragmentCount: diary.fragment_count,
      });
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  /** 简易 Markdown → HTML (标题 + 段落 + 加粗) */
  markdownToHtml(md) {
    if (!md) return '';
    return md
      .split('\n')
      .map(line => {
        if (line.startsWith('# '))  return `<h2>${line.slice(2)}</h2>`;
        if (line.startsWith('## ')) return `<h3>${line.slice(3)}</h3>`;
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        line = line.replace(/\*(.+?)\*/g, '<em>$1</em>');
        return line ? `<p>${line}</p>` : '';
      })
      .join('');
  },
});
