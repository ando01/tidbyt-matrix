"""Custom clock app with color themes — time + day + date on one screen"""

import time
import colorsys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class CustomClockApp(MatrixApp):
    """Clock showing time, day of week, and date stacked on one 64×32 frame"""

    COLOR_MAP = {
        'blue':  (100, 150, 255),
        'green': (100, 255, 100),
        'red':   (255, 100, 100),
        'white': (255, 255, 255),
    }

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("CustomClock", config)
        self.color_theme = config.config.get('color_theme', 'blue') if config else 'blue'
        self.format_24h = config.config.get('format_24h', False) if config else False

    def _get_color(self, frame_num: int):
        if self.color_theme == 'rainbow':
            hue = (frame_num / 12.0) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255))
        return self.COLOR_MAP.get(self.color_theme, (100, 150, 255))

    def get_frames(self) -> List[Image.Image]:
        frames = []
        now = datetime.now()

        try:
            font_time = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
            font_ampm = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 9)
            font_info = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 10)
        except Exception:
            font_time = font_ampm = font_info = ImageFont.load_default()

        if self.format_24h:
            time_str = now.strftime("%H:%M")
            ampm = None
        else:
            time_str = now.strftime("%I:%M").lstrip('0') or '12:00'
            ampm = now.strftime("%p")

        day_str  = now.strftime("%A")     # Wednesday
        date_str = now.strftime("%b %-d") # Mar 4

        for i in range(12):
            color = self._get_color(i)
            dim = tuple(max(0, c - 90) for c in color)

            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Row 1 — time (14px) at top
            draw.text((2, 0), time_str, fill=color, font=font_time)
            if ampm:
                # AM/PM flush against the time digits, same y baseline
                bbox = draw.textbbox((0, 0), time_str, font=font_time)
                tw = bbox[2] - bbox[0]
                draw.text((tw + 3, 0), ampm, fill=dim, font=font_ampm)

            # Row 2 — day of week (10px)
            draw.text((2, 10), day_str, fill=dim, font=font_info)

            # Row 3 — date (10px)
            draw.text((2, 20), date_str, fill=dim, font=font_info)

            frames.append(img)

        return frames

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 10
