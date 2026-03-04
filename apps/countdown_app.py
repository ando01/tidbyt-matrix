"""Countdown app — days until/since configurable events"""

import time
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class CountdownApp(MatrixApp):
    """Shows days until (or since) named events"""

    DEFAULT_EVENTS = [{"name": "Summer", "date": "2026-06-21"}]

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Countdown", config)
        self.events = config.config.get('events', self.DEFAULT_EVENTS) if config else self.DEFAULT_EVENTS

    def _days_delta(self, date_str: str):
        """Return (days, is_future). Positive = future, negative = past."""
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
            delta = (target - date.today()).days
            return delta
        except Exception:
            return 0

    def get_frames(self) -> List[Image.Image]:
        frames = []
        try:
            font_name = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
            font_count = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
            font_label = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
        except Exception:
            font_name = font_count = font_label = ImageFont.load_default()

        for event in self.events:
            name = event.get('name', 'Event')
            date_str = event.get('date', '2026-01-01')
            delta = self._days_delta(date_str)

            if delta >= 0:
                count_str = str(delta)
                label_str = "days to go"
            else:
                count_str = str(abs(delta))
                label_str = "days ago"

            for _ in range(6):
                img = Image.new('RGB', (64, 32), (0, 0, 0))
                draw = ImageDraw.Draw(img)

                # Event name — yellow, top
                name_display = name[:10]
                bbox = draw.textbbox((0, 0), name_display, font=font_name)
                nx = (64 - (bbox[2] - bbox[0])) // 2
                draw.text((nx, 1), name_display, fill=(255, 220, 0), font=font_name)

                # Day count — white, large, center
                bbox = draw.textbbox((0, 0), count_str, font=font_count)
                cx = (64 - (bbox[2] - bbox[0])) // 2
                draw.text((cx, 10), count_str, fill=(255, 255, 255), font=font_count)

                # Label — dimmer, bottom
                bbox = draw.textbbox((0, 0), label_str, font=font_label)
                lx = (64 - (bbox[2] - bbox[0])) // 2
                draw.text((lx, 22), label_str, fill=(150, 150, 150), font=font_label)

                frames.append(img)

        return frames if frames else self._no_events_frame()

    def _no_events_frame(self) -> List[Image.Image]:
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
        except Exception:
            font = ImageFont.load_default()
        img = Image.new('RGB', (64, 32), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 10), "No events", fill=(150, 150, 150), font=font)
        return [img] * 6

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 3600
