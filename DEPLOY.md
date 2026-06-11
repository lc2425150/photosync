# PhotoSync 部署指南

## 方式一：Docker Compose 部署（推荐）

### 1. 准备 docker-compose.yml

```yaml
services:
  photosync:
    build: .
    image: photosync:latest
    container_name: photosync
    ports:
      - "8932:8932"
    volumes:
      - /media:/media:ro
      - /mnt:/mnt:ro
      - /run/media:/run/media:ro
      - /volume2/照片:/photos:rw       # ← 改成你的 NAS 照片目录
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
      - POLL_INTERVAL=5
      - PHOTOS_MOUNT_HOST_PATH=/volume2/照片  # ← 改成你的 NAS 路径
    restart: unless-stopped
```

### 2. 构建并启动

```bash
# 构建镜像
docker compose build

# 启动容器
docker compose up -d

# 查看日志
docker compose logs -f
```

### 3. 访问

打开 http://你的NAS_IP:8932

---

## 方式二：纯 Docker 命令

```bash
# 构建镜像
docker build -t photosync:latest .

# 运行容器
docker run -d \
  --name photosync \
  --restart unless-stopped \
  -p 8932:8932 \
  -v /media:/media:ro \
  -v /mnt:/mnt:ro \
  -v /run/media:/run/media:ro \
  -v /volume2/照片:/photos:rw \
  -v ./data:/app/data \
  -e TZ=Asia/Shanghai \
  -e POLL_INTERVAL=5 \
  -e PHOTOS_MOUNT_HOST_PATH=/volume2/照片 \
  photosync:latest
```

---

## 方式三：从镜像仓库拉取（待发布后可用）

```bash
# 登录 GitHub Container Registry
echo "你的_GITHUB_TOKEN" | docker login ghcr.io -u 你的_GITHUB用户名 --password-stdin

# 拉取镜像
docker pull ghcr.io/lc2425150/photosync:latest

# 运行
docker run -d --name photosync \
  --restart unless-stopped \
  -p 8932:8932 \
  -v /media:/media:ro \
  -v /mnt:/mnt:ro \
  -v /run/media:/run/media:ro \
  -v /volume2/照片:/photos:rw \
  -v ./data:/app/data \
  -e TZ=Asia/Shanghai \
  -e POLL_INTERVAL=5 \
  -e PHOTOS_MOUNT_HOST_PATH=/volume2/照片 \
  ghcr.io/lc2425150/photosync:latest
```

---

## 配置说明

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `TZ` | `Asia/Shanghai` | 时区 |
| `POLL_INTERVAL` | `5` | 储存卡轮询间隔（秒） |
| `PHOTOS_MOUNT_HOST_PATH` | `/volume2/照片` | NAS 上的照片目录真实路径 |
| `DEBUG` | `false` | 调试模式 |

| 卷挂载 | 说明 |
|--------|------|
| `/media:/media:ro` | 储存卡挂载路径（只读） |
| `/volume2/照片:/photos:rw` | 照片存储目标路径 |
| `./data:/app/data` | 数据库和缩略图持久化 |

---

## 常见问题

**Q: 页面打开是空白？**
A: 尝试访问 `http://你的IP:8932/static/index.html`

**Q: 检测不到储存卡？**
A: 检查 NAS 把 USB 设备挂载到了哪个路径（通常是 `/media`、`/mnt` 或 `/run/media`）

**Q: 如何修改默认照片目录？**
A: 修改 `PHOTOS_MOUNT_HOST_PATH` 和对应的 volumes 映射即可
