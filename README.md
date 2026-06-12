# PhotoSync

> NAS 相机储存卡自动同步系统  
> 插卡即备，自动将相机照片/视频同步到 NAS

![dashboard](https://img.shields.io/badge/status-stable-green)
![docker](https://img.shields.io/badge/docker-ready-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 功能特性

- ✅ **自动检测** — USB 插入储存卡后自动识别（DCIM 检测）
- ✅ **即插即备** — 配置好自动同步规则，插卡即自动备份
- ✅ **手动同步** — 也支持手动选择卡和配置触发同步
- ✅ **照片+视频** — 支持 JPEG、RAW、DNG、MP4、MOV 等常见格式
- ✅ **多种归档** — 按日期归档 / 保留原目录结构 / 自定义模板
- ✅ **SHA256 去重** — 重复文件自动跳过，避免重复备份
- ✅ **实时进度** — WebSocket 推送同步进度、速度、剩余时间
- ✅ **通知集成** — Telegram / 钉钉 / 企业微信 / 邮件 / Webhook
- ✅ **照片画廊** — Web 端浏览已同步的照片
- ✅ **NAS 路径映射** — 直接填写 NAS 上的文件夹路径，系统自动转换

---

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/lc2425150/photosync.git
cd photosync

# 2. 修改 docker-compose.yml 中的路径
#    - /volume2/Photos → 改成你的 NAS 照片存储目录
#    - PHOTOS_MOUNT_HOST_PATH → 改成同样的路径

# 3. 构建并启动
docker compose build
docker compose up -d

# 4. 访问 http://你的NAS_IP:8932
```

### 方式二：一键部署脚本

```bash
# 默认照片目录 /volume2/Photos
./deploy.sh

# 自定义照片目录
PHOTOS_DIR=/volume1/photo ./deploy.sh

# 自定义端口
PORT=8080 ./deploy.sh
```

### 方式三：纯 Docker 命令

```bash
# 构建
docker build -t photosync:latest .

# 运行
docker run -d --name photosync --restart unless-stopped -p 8932:8932 \
  --mount type=bind,source=/media,target=/media,readonly,bind-propagation=rslave \
  --mount type=bind,source=/mnt,target=/mnt,readonly,bind-propagation=rslave \
  --mount type=bind,source=/run/media,target=/run/media,readonly,bind-propagation=rslave \
  -v /volume2/Photos:/photos:rw \
  -v ./data:/app/data \
  -e TZ=Asia/Shanghai \
  -e POLL_INTERVAL=5 \
  -e PHOTOS_MOUNT_HOST_PATH=/volume2/Photos \
  photosync:latest
```

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | `Asia/Shanghai` | 时区 |
| `POLL_INTERVAL` | `5` | 储存卡轮询间隔（秒） |
| `PHOTOS_MOUNT_HOST_PATH` | `/volume2/Photos` | NAS 上的照片目录真实路径 |
| `DEBUG` | `false` | 调试模式 |

### 卷挂载

| 容器路径 | 说明 |
|---------|------|
| `/media` `:ro` | 储存卡自动挂载路径（只读） |
| `/mnt` `:ro` | 储存卡自动挂载路径（只读） |
| `/run/media` `:ro` | 储存卡自动挂载路径（只读） |
| `/photos` `:rw` | 照片存储目标路径 |
| `/app/data` | 数据库和缩略图持久化 |

> ⚠️ **重要**：`/mnt`、`/media`、`/run/media` 使用 `rslave` 传播模式，
> 确保宿主机上 USB 设备挂载的事件能透传到容器内。

---

## 使用指南

### 首次使用

1. 打开 `http://你的NAS_IP:8932`
2. 进入「系统设置」→ 确认「扫描路径」包含你的 NAS USB 挂载路径
   - UGREEN NAS：添加 `/mnt/@usb`
3. 进入「同步配置」→ 新建配置
   - 匹配方式：选「插卡即同步」或「手动」
   - 目标目录：填入 NAS 上的完整路径（如 `/volume2/Photos/相机备份`）
   - 勾选「同步视频」以同步视频文件
4. 插入储存卡，系统自动检测并同步

### 手动同步

- **储存卡浏览器**：每张卡右下角「手动同步」按钮
- **同步配置**：每个配置卡片底部「🔄 手动同步」按钮

### 停止同步

- **仪表盘**：同步进度卡片右上角「停止同步」按钮

---

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy (async) + SQLite WAL
- **前端**: Vue 3 + Vite + Tailwind CSS
- **部署**: Docker 多阶段构建 (~180MB)

---

## 目录结构

```
photosync/
├── deploy.sh                    # 一键部署脚本
├── docker-compose.yml           # Docker Compose 配置
├── Dockerfile                   # 多阶段构建
├── DEPLOY.md                    # 部署指南
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置
│   │   ├── models.py            # ORM 模型
│   │   ├── schemas.py           # Pydantic 响应模型
│   │   ├── path_mapper.py       # NAS↔容器路径映射
│   │   ├── routers/             # API 路由
│   │   └── services/            # 业务逻辑
│   └── tests/                   # 测试
└── frontend/
    └── src/
        ├── views/               # 页面组件
        ├── components/          # 通用组件
        └── api/                 # API 客户端
```

---

## 开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8932

# 前端
cd frontend
npm install
npm run dev
```

## 许可证

MIT
