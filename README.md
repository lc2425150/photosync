<p align="center">
  <h1 align="center">PhotoSync</h1>
  <p align="center">即插即备 — NAS 相机储存卡自动同步系统</p>
  <p align="center">
    <em>Plug in an SD card. Photos appear on your NAS. Automatically.</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/vue-3.4-brightgreen?logo=vue.js" alt="Vue 3">
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker" alt="Docker">
</p>

---

## 概述

**PhotoSync** 是一个运行在 NAS 上的 Docker 应用，解决摄影师的真实痛点：

> 每次拍完照片，把 SD 卡插到 NAS 的 USB 口，照片**自动**按日期归档到指定目录，无需手动拷贝。

### 工作流程

```
📸 插入储存卡
   ↓
🔍 自动检测（DCIM 签名 + 挂载点检测）
   ↓
📋 匹配同步配置（按卷标 / 自动 / 手动）
   ↓
📂 SHA256 去重 → 按日期归档 → 校验完整性
   ↓
🖼️ 生成缩略图 → WebSocket 推送到浏览器
   ↓
🔔 通知（Telegram / 钉钉 / 邮件 / Webhook）
```

---

## 功能特性

| 类别 | 功能 |
|------|------|
| **检测** | 自动检测 USB 储存卡插入（挂载点 + DCIM 签名，不会误识别 NAS 系统卷） |
| **归档** | 按日期 `YYYY/mm/dd` / 原目录结构 / 自定义模板 (`{Y}/{m}/{d}/{filename}`) |
| **去重** | SHA256 哈希全局去重，同一张照片不会重复同步 |
| **筛选** | 按文件类型（RAW/JPEG/视频）、自定义扩展名过滤 |
| **冲突** | 跳过 / 覆盖 / 自动重命名 / 保留两者 |
| **校验** | 同步后 SHA256 校验，确保数据完整 |
| **侧写文件** | 自动同步 XMP/PP3 等侧写文件 |
| **队列** | 多卡同时插入→排队处理，互不干扰 |
| **实时** | WebSocket 推送进度（当前文件、速度、ETA） |
| **通知** | Telegram / 钉钉 / 企业微信 / 邮件 / Webhook |
| **画廊** | 缩略图浏览已同步照片（支持 RAW 嵌入式预览） |
| **配置** | 多配置模板：不同相机用不同规则 |
| **预览** | Dry-Run 模式：先看会同步哪些文件，再执行 |
| **主题** | 深色 / 浅色模式 |

---

## 快速开始

### 前置要求

- 一台 **NAS**（绿联 / 群晖 / 威联通 / Unraid / 任何支持 Docker 的 NAS）
- **Docker** + **Docker Compose** 已安装
- NAS 的 USB 口能识别到相机储存卡

### 部署

```bash
# 1. 克隆
git clone https://github.com/lc2425150/photosync.git
cd photosync

# 2. 修改 docker-compose.yml 中的卷挂载路径
#    - /media → 你的 USB 挂载点目录
#    - /volume2/照片 → 你的照片存储目录

# 3. 构建并启动
docker compose up -d --build

# 4. 查看日志
docker logs -f photosync
```

### 首次使用

1. 浏览器打开 `http://<NAS_IP>:8932`
2. 跟随引导向导完成初始化
3. 插入相机储存卡 → 照片自动同步！

---

## 截图

| 仪表盘 | 同步配置 | 画廊 |
|--------|----------|------|
| _(TBD)_ | _(TBD)_ | _(TBD)_ |

---

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | `Asia/Shanghai` | 时区 |
| `PUID` | `1000` | 运行用户 UID |
| `PGID` | `100` | 运行用户 GID |
| `POLL_INTERVAL` | `5` | USB 轮询间隔（秒） |
| `DEBUG` | `false` | 调试模式 |

### 目录挂载

```yaml
volumes:
  - /media:/media:ro          # USB 储存卡挂载点（只读）
  - /mnt:/mnt:ro              # 备选挂载点
  - /volume2/照片:/photos:rw # 照片同步目标（读写）
  - ./data:/app/data          # 数据库 + 配置持久化
```

---

## API

启动后访问 `http://<NAS_IP>:8932/docs` 查看 Swagger 文档。

### 核心端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/cards` | 列出已检测到的储存卡 |
| `GET` | `/api/v1/profiles` | 同步配置列表 |
| `POST` | `/api/v1/sync/trigger` | 触发同步 |
| `GET` | `/api/v1/sync/status` | 同步进度 |
| `GET` | `/api/v1/gallery` | 照片画廊 |
| `GET` | `/api/v1/system/health` | 健康检查 |

---

## 技术栈

```
┌─────────────────────────────────────┐
│          Frontend (Vue 3)           │
│   Tailwind CSS · Pinia · Vue Router │
├─────────────────────────────────────┤
│      Backend (Python FastAPI)       │
│  SQLAlchemy async · WebSocket ·     │
│  Pillow · httpx · Pydantic          │
├─────────────────────────────────────┤
│        Docker (multi-stage)         │
│  Python 3.11-slim · Node 20 (build) │
│  ~200MB image · healthcheck         │
└─────────────────────────────────────┘
```

### 为什么是这些技术？

- **FastAPI + async** → 同步时不会阻塞 Web UI
- **SQLite WAL** → 零运维数据库，一个文件搞定
- **WebSocket** → 浏览器实时看到同步进度
- **Vue 3 + Tailwind** → 轻量前端，适合 NAS 低配环境

---

## 与现有方案对比

| 功能 | **PhotoSync** | File-Vacuum-5000 | Immich | PhotoPrism |
|------|:---:|:---:|:---:|:---:|
| USB 卡检测 | ✅ | ✅ | ❌ | ❌ |
| 即插即同步 | ✅ | ✅ | ❌ | ❌ |
| Docker | ✅ | ❌ | ✅ | ✅ |
| 按日期归档 | ✅ | ✅ | ✅ | ✅ |
| SHA256 去重 | ✅ | ❌ | ✅ | ✅ |
| RAW 支持 | ✅ | ❌ | ✅ | ✅ |
| Web UI | ✅ | ❌ | ✅ | ✅ |
| 通知 | ✅ | ✅ | ✅ | ❌ |
| 冲突策略 | ✅ 4种 | ❌ | N/A | N/A |

**PhotoSync 专注于一个场景并做到极致：** NAS 上的相机储存卡即插即备。

---

## 开发

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8932

# 前端开发（需要 Node.js 18+）
cd frontend
npm install
npm run dev
```

---

## 许可证

[MIT](LICENSE)

## 作者

[@lc2425150](https://github.com/lc2425150)
