"""Custom clock app with color themes"""

import time
import colorsys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class CustomClockApp(MatrixApp):
    """Clock with configurable color themes and 12/24hr format"""

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
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 20)
            font_med = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 13)
        except Exception:
            font_large = font_med = ImageFont.load_default()

        # Slide 1: Time (6 frames = 3s)
        if self.format_24h:
            time_str = now.strftime("%H:%M")
        else:
            time_str = now.strftime("%I:%M").lstrip('0') or '12:00'
            ampm = now.strftime("%p")

        for i in range(6):
            color = self._get_color(i)
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), time_str, font=font_large)
            x = (64 - (bbox[2] - bbox[0])) // 2
            y = (32 - (bbox[3] - bbox[1])) // 2
            if not self.format_24h:
                y = max(1, y - 4)
            draw.text((x, y), time_str, fill=color, font=font_large)
            if not self.format_24h:
                ampm_color = tuple(max(0, c - 100) for c in color)
                draw.text((x + (bbox[2] - bbox[0]) + 2, y + 6), ampm, fill=ampm_color, font=font_med)
            frames.append(img)

        # Slide 2: Date (6 frames = 3s)
        date_str = now.strftime("%a %b %d").replace(' 0', ' ')
        for i in range(6):
            color = self._get_color(i + 6)
            dim = tuple(max(0, c - 80) for c in color)
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), date_str, font=font_med)
            x = (64 - (bbox[2] - bbox[0])) // 2
            y = (32 - (bbox[3] - bbox[1])) // 2
            draw.text((x, y), date_str, fill=dim, font=font_med)
            frames.append(img)

        return frames

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 10
