"""Custom clock app with color themes — single-screen time + date layout"""

import time
import colorsys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class CustomClockApp(MatrixApp):
    """Clock with time + date on one screen, configurable color themes and 12/24hr format"""

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
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
            font_ampm = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 10)
            font_date = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
        except Exception:
            font_time = font_ampm = font_date = ImageFont.load_default()

        if self.format_24h:
            time_str = now.strftime("%H:%M")
            ampm = None
        else:
            time_str = now.strftime("%I:%M").lstrip('0') or '12:00'
            ampm = now.strftime("%p")

        # "Wed Mar 4" — no leading zero on day
        date_str = now.strftime("%a %b %-d")

        for i in range(12):
            color = self._get_color(i)
            dim = tuple(max(0, c - 90) for c in color)

            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # --- Time row (top) ---
            bbox = draw.textbbox((0, 0), time_str, font=font_time)
            tw = bbox[2] - bbox[0]
            draw.text((2, 1), time_str, fill=color, font=font_time)

            if ampm:
                # AM/PM to the right of the time, vertically centered on it
                draw.text((tw + 4, 5), ampm, fill=dim, font=font_ampm)

            # --- Date row (bottom) ---
            draw.text((2, 21), date_str, fill=dim, font=font_date)

            frames.append(img)

        return frames

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 10
