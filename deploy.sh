#!/usr/bin/env bash
# ============================================================================
# PhotoSync — 一键部署脚本
#
# 用法:
#   ./deploy.sh                           # 本地构建并运行
#   PHOTOS_DIR=/volume1/photo ./deploy.sh # 自定义照片目录
#   PORT=8080 ./deploy.sh                 # 自定义端口
#
# 前置条件: 需要安装 Docker
# ============================================================================
set -euo pipefail

IMAGE_NAME="photosync"
IMAGE_TAG="latest"
PORT="${PORT:-8932}"
PHOTOS_DIR="${PHOTOS_DIR:-/volume2/Photos}"
DATA_DIR="${DATA_DIR:-./data}"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }

cd "$(dirname "$0")"

info "构建 Docker 镜像 ..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

mkdir -p "$DATA_DIR"

info "启动容器 ..."
docker rm -f "${IMAGE_NAME}" 2>/dev/null || true

docker run -d \
  --name "${IMAGE_NAME}" \
  --restart unless-stopped \
  -p "${PORT}:8932" \
  --mount type=bind,source=/media,target=/media,readonly,bind-propagation=rslave \
  --mount type=bind,source=/mnt,target=/mnt,readonly,bind-propagation=rslave \
  --mount type=bind,source=/run/media,target=/run/media,readonly,bind-propagation=rslave \
  -v "${PHOTOS_DIR}:/photos:rw" \
  -v "$(realpath "$DATA_DIR")":/app/data \
  -e TZ="${TZ:-Asia/Shanghai}" \
  -e POLL_INTERVAL="${POLL_INTERVAL:-5}" \
  -e PHOTOS_MOUNT_HOST_PATH="${PHOTOS_DIR}" \
  "${IMAGE_NAME}:${IMAGE_TAG}"

echo ""
ok "部署完成！"
info "访问地址: http://localhost:${PORT}"
info "照片目录: ${PHOTOS_DIR}"
info ""
info "配置方法:"
info "  1. 打开浏览器访问 http://localhost:${PORT}"
info "  2. 在「设置」中确认扫描路径包含 /mnt/@usb（UGREEN NAS）"
info "  3. 在「同步配置」中新建配置，目标目录填入 NAS 路径"
