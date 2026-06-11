#!/usr/bin/env bash
# ============================================================================
# PhotoSync — 一键部署脚本
# 构建 Docker 镜像并部署到目标 NAS（或任何 Docker 宿主机）
#
# 用法:
#   ./deploy.sh                        # 本地构建并运行
#   ./deploy.sh --remote user@host     # 构建并部署到远程主机
#   ./deploy.sh --remote user@host -p 8932  # 指定端口
#
# 前置条件:
#   - Docker（本地或目标主机上）
#   - 如使用远程部署，目标主机需能通过 SSH 密码认证（或配置好 key）
# ============================================================================
set -euo pipefail

# ── 默认配置 ──────────────────────────────────────────────────────────
IMAGE_NAME="photosync"
IMAGE_TAG="latest"
PORT="${PORT:-8932}"
PHOTOS_MOUNT="${PHOTOS_MOUNT:-/volume2/照片}"
DATA_DIR="${DATA_DIR:-./data}"
REMOTE_USER=""
REMOTE_HOST=""
SSH_PASSWORD="${SSH_PASSWORD:-}"

# ── 颜色 ──────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

# ── 参数解析 ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)  REMOTE_USER="${2%%@*}"; REMOTE_HOST="${2#*@}"; shift 2 ;;
    -p|--port) PORT="$2"; shift 2 ;;
    --password) SSH_PASSWORD="$2"; shift 2 ;;
    -h|--help)
      sed -n '3,11p' "$0"
      exit 0 ;;
    *) err "未知参数: $1"; exit 1 ;;
  esac
done

# ── 检测依赖 ──────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  err "Docker 未安装，请先安装 Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

# ── 获取项目根目录 ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

info "🛠  构建 Docker 镜像 ${IMAGE_NAME}:${IMAGE_TAG} ..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

ok "✅ 镜像构建完成"

# ── 准备数据目录 ──────────────────────────────────────────────────────
mkdir -p "$DATA_DIR"

# ── 部署函数 ──────────────────────────────────────────────────────────
run_container() {
  local host_photos="$1"
  info "🚀 启动容器 ${IMAGE_NAME}:${IMAGE_TAG} ..."

  docker rm -f "${IMAGE_NAME}" 2>/dev/null || true

  docker run -d \
    --name "${IMAGE_NAME}" \
    --restart unless-stopped \
    -p "${PORT}:8932" \
    -v /media:/media:ro \
    -v /mnt:/mnt:ro \
    -v /run/media:/run/media:ro \
    -v "${host_photos}:/photos:rw" \
    -v "$(realpath "$DATA_DIR")":/app/data \
    -e TZ="${TZ:-Asia/Shanghai}" \
    -e POLL_INTERVAL="${POLL_INTERVAL:-5}" \
    -e PHOTOS_MOUNT_HOST_PATH="${host_photos}" \
    "${IMAGE_NAME}:${IMAGE_TAG}"

  echo ""
  ok "✅ 容器已启动！"
  info "🌐 访问地址: http://localhost:${PORT}"
  info "📸 照片目录: ${host_photos}"
  info "📁 数据目录: $(realpath "$DATA_DIR")"
  info ""
  info "💡 如果页面空白，请尝试: http://localhost:${PORT}/static/index.html"
}

# ── 远程部署 ─────────────────────────────────────────────────────────
if [[ -n "$REMOTE_HOST" ]]; then
  if ! command -v sshpass &>/dev/null && [[ -z "$SSH_PASSWORD" ]]; then
    warn "sshpass 未安装，将使用 SSH key 认证（请确保已配置免密登录）"
  fi

  info "📦 打包镜像并传送到 ${REMOTE_USER}@${REMOTE_HOST} ..."

  # Save image to tarball
  docker save "${IMAGE_NAME}:${IMAGE_TAG}" | gzip > /tmp/"${IMAGE_NAME}".tar.gz

  # Upload via scp (use sshpass if password provided)
  local scp_cmd="scp -o StrictHostKeyChecking=no"
  if [[ -n "$SSH_PASSWORD" ]]; then
    sshpass -p "$SSH_PASSWORD" $scp_cmd /tmp/"${IMAGE_NAME}".tar.gz "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"
  else
    $scp_cmd /tmp/"${IMAGE_NAME}".tar.gz "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"
  fi
  ok "镜像已上传"

  # Build remote command
  local remote_cmd
  remote_cmd="docker load -i /tmp/${IMAGE_NAME}.tar.gz && "
  remote_cmd+="docker rm -f ${IMAGE_NAME} 2>/dev/null; "
  remote_cmd+="docker run -d --name ${IMAGE_NAME} --restart unless-stopped "
  remote_cmd+="-p ${PORT}:8932 "
  remote_cmd+="-v /media:/media:ro -v /mnt:/mnt:ro -v /run/media:/run/media:ro "
  remote_cmd+="-v ${PHOTOS_MOUNT}:/photos:rw "
  remote_cmd+="-v ${DATA_DIR}:/app/data "
  remote_cmd+="-e TZ=${TZ:-Asia/Shanghai} -e POLL_INTERVAL=${POLL_INTERVAL:-5} "
  remote_cmd+="-e PHOTOS_MOUNT_HOST_PATH=${PHOTOS_MOUNT} "
  remote_cmd+="${IMAGE_NAME}:${IMAGE_TAG}"

  info "🖥️  在远程主机上启动容器 ..."
  local ssh_cmd="ssh -o StrictHostKeyChecking=no"
  if [[ -n "$SSH_PASSWORD" ]]; then
    sshpass -p "$SSH_PASSWORD" $ssh_cmd "${REMOTE_USER}@${REMOTE_HOST}" "$remote_cmd"
  else
    $ssh_cmd "${REMOTE_USER}@${REMOTE_HOST}" "$remote_cmd"
  fi

  echo ""
  ok "✅ 远程部署完成！"
  info "🌐 访问地址: http://${REMOTE_HOST}:${PORT}"
  exit 0
fi

# ── 本地部署 ─────────────────────────────────────────────────────────
run_container "$PHOTOS_MOUNT"
