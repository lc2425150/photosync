"""
PhotoSync — host ↔ container path translation.

Lets users enter NAS host paths (e.g. ``/volume2/照片/相机备份``)
while the app stores and uses container paths (e.g. ``/photos/相机备份``).
"""

from __future__ import annotations

from app.config import settings

# The container-internal mount point for photos
_CONTAINER_MOUNT = "/photos"


def to_host(container_path: str) -> str:
    """Convert a container-internal path to the corresponding NAS host path.

    Example:
        ``/photos/相机备份`` → ``/volume2/照片/相机备份``
    """
    host_base = settings.photos_mount_host_path.rstrip("/")
    if container_path.startswith(_CONTAINER_MOUNT):
        suffix = container_path[len(_CONTAINER_MOUNT):]  # strip "/photos"
        return host_base + suffix
    return container_path


def to_container(host_path: str) -> str:
    """Convert a NAS host path to the corresponding container-internal path.

    Example:
        ``/volume2/照片/相机备份`` → ``/photos/相机备份``
    """
    host_base = settings.photos_mount_host_path.rstrip("/")
    if host_path.startswith(host_base):
        suffix = host_path[len(host_base):]
        return _CONTAINER_MOUNT + suffix
    return host_path
