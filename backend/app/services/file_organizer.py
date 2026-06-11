"""
PhotoSync — file path organizer that computes destination paths
based on sync mode and metadata.
"""

from __future__ import annotations

import os
import datetime
from typing import Optional

from app.services.file_scanner import sanitize_filename


class FileOrganizer:
    """Map source files to destination paths."""

    def __init__(
        self,
        destination: str,
        sync_mode: str = "date",
        custom_template: Optional[str] = None,
    ) -> None:
        self.destination = destination
        self.sync_mode = sync_mode
        self.custom_template = custom_template

    def get_dest_path(
        self,
        filename: str,
        mtime: float,
        exif_date: Optional[str] = None,
        camera_model: Optional[str] = None,
    ) -> str:
        safe = sanitize_filename(filename)
        dt = self._get_dt(mtime, exif_date)

        if self.sync_mode == "original":
            return os.path.join(self.destination, safe)

        if self.sync_mode == "custom" and self.custom_template:
            return self._apply_template(safe, dt, camera_model)

        # Default: date-based layout  YYYY/mm/dd/filename
        return os.path.join(
            self.destination,
            dt.strftime("%Y"),
            dt.strftime("%m"),
            dt.strftime("%d"),
            safe,
        )

    def _get_dt(self, mtime: float, exif_date: Optional[str] = None) -> datetime.datetime:
        if exif_date:
            try:
                return datetime.datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
        return datetime.datetime.fromtimestamp(mtime)

    def _apply_template(
        self,
        safe: str,
        dt: datetime.datetime,
        camera_model: Optional[str] = None,
    ) -> str:
        t = self.custom_template or "{Y}/{m}/{d}/{filename}"
        t = t.replace("{Y}", dt.strftime("%Y"))
        t = t.replace("{m}", dt.strftime("%m"))
        t = t.replace("{d}", dt.strftime("%d"))
        t = t.replace("{H}", dt.strftime("%H"))
        t = t.replace("{M}", dt.strftime("%M"))
        t = t.replace("{S}", dt.strftime("%S"))
        t = t.replace("{filename}", safe)
        if camera_model:
            t = t.replace("{model}", sanitize_filename(camera_model))
        return os.path.join(self.destination, t.lstrip("/"))
