# 碎片日记 (Fragment Diary)

微信小程序 + Python 后端。随时记录文字、语音、照片碎片，每天晚上 AI 自动合成一篇完整日记。

## 架构

```
微信小程序 ──► FastAPI 后端 ──► Supabase (存储碎片)
                                    │
                     APScheduler (每晚 22:00) ──► Claude API (合成日记)
                                    │
                               Supabase (存储日记) ──► 用户打开小程序查看
```

## 项目结构

```
fragment-diary-bot/
├── main.py                         # FastAPI 服务入口
├── config.py                       # 环境变量配置
├── requirements.txt
├── .env.example
│
├── api/                            # REST API 路由
│   ├── auth.py                     # 微信登录 + JWT
│   ├── deps.py                     # 鉴权依赖
│   ├── fragments.py                # 碎片 CRUD
│   └── diaries.py                  # 日记读取 + 生成
│
├── services/
│   ├── supabase_client.py          # 数据库 & 文件存储
│   └── claude_service.py           # AI 日记合成
│
├── scheduler/
│   └── daily_diary.py              # 每日定时任务
│
├── models/
│   ├── __init__.py                 # Pydantic 数据模型
│   └── schema.sql                  # Supabase 建表 SQL
│
├── utils/
│   └── logger.py
│
└── weapp/                          # 微信小程序前端
    ├── app.js / app.json / app.wxss
    ├── utils/api.js                # 请求封装
    └── pages/
        ├── index/                  # 碎片记录页（首页）
        ├── diary/                  # 日记列表页
        ├── diary-detail/           # 日记详情页
        └── profile/                # 个人中心
```

## 快速开始

### 1. 准备外部服务

| 服务 | 获取方式 |
|------|----------|
| 微信小程序 AppID | [mp.weixin.qq.com](https://mp.weixin.qq.com) 注册小程序 |
| Claude API Key | [console.anthropic.com](https://console.anthropic.com) |
| Supabase 项目 | [supabase.com](https://supabase.com) 免费创建 |

### 2. 初始化数据库

在 Supabase SQL Editor 中运行 `models/schema.sql`，并在 Storage 中创建名为 `fragments` 的 bucket。

### 3. 启动后端

```bash
cd fragment-diary-bot
pip install -r requirements.txt
cp .env.example .env   # 编辑填入你的 keys
python main.py         # 启动在 http://localhost:8000
```

API 文档自动生成在 `http://localhost:8000/docs`。

### 4. 配置小程序

1. 用微信开发者工具打开 `weapp/` 目录
2. 在 `app.js` 中修改 `baseUrl` 为你的后端地址
3. 在微信公众平台后台配置服务器域名白名单

### 5. 部署后端（推荐）

推荐使用带 HTTPS 的云服务器（小程序要求 HTTPS）：阿里云、腾讯云轻量服务器，或 Railway / Render 等 PaaS。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 微信登录，换取 token |
| POST | /api/fragments/text | 记录文字碎片 |
| POST | /api/fragments/photo | 上传照片碎片 |
| POST | /api/fragments/voice | 上传语音碎片 |
| GET  | /api/fragments/today | 获取今日碎片列表 |
| POST | /api/diaries/generate | 手动生成日记 |
| GET  | /api/diaries/today | 获取今日日记 |
| GET  | /api/diaries/history | 获取历史日记列表 |
| GET  | /api/diaries/{date} | 获取指定日期日记 |

## 待扩展

- [ ] 语音转文字（Whisper API）
- [ ] 微信订阅消息推送（日记生成通知）
- [ ] 日记风格自定义
- [ ] 每周/月度 AI 总结
- [ ] 情绪分析标签
- [ ] 导出为 PDF
