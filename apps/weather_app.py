"""Combined weather app with large pixel-art animated icons.

Layout matches Tidbyt-style: large animated icon fills the display,
day abbreviation bottom-left, current temperature bottom-right.
A brief high/low slide follows the animation loop.
"""

import time
import math
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class WeatherApp(MatrixApp):
    """Weather display with large pixel-art animations and minimal corner text"""

    WMO_CODES = {
        0: "Clear", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy Fog",
        51: "Lt Drizzle", 53: "Drizzle", 55: "Hvy Drizzle",
        61: "Lt Rain", 63: "Rain", 65: "Hvy Rain",
        71: "Lt Snow", 73: "Snow", 75: "Hvy Snow", 77: "Snow Grains",
        80: "Showers", 81: "Showers", 82: "Hvy Showers",
        85: "Snow Shwrs", 86: "Hvy Snow",
        95: "Tstorm", 96: "Tstorm", 99: "Hvy Storm",
    }

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Weather", config)
        self.zip_code = config.config.get('zip_code', '02134') if config else '02134'
        self.lat = None
        self.lon = None
        self._resolve_location()

    def _resolve_location(self):
        try:
            resp = requests.get(f"https://api.zippopotam.us/us/{self.zip_code}", timeout=5)
            if resp.status_code == 200:
                place = resp.json()['places'][0]
                self.lat = float(place['latitude'])
                self.lon = float(place['longitude'])
                return
        except Exception:
            pass
        try:
            url = (f"https://geocoding-api.open-meteo.com/v1/search"
                   f"?name={self.zip_code}&count=1&country=US&language=en&format=json")
            data = requests.get(url, timeout=5).json()
            if data.get('results'):
                self.lat = data['results'][0]['latitude']
                self.lon = data['results'][0]['longitude']
        except Exception:
            pass

    def _fetch_weather(self):
        if self.lat is None:
            self._resolve_location()
        if self.lat is None:
            return None
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.lat}&longitude={self.lon}"
                f"&current=temperature_2m,weather_code,relative_humidity_2m"
                f"&daily=temperature_2m_max,temperature_2m_min"
                f"&temperature_unit=fahrenheit&timezone=auto&forecast_days=1"
            )
            data = requests.get(url, timeout=5).json()
            current = data.get('current', {})
            daily = data.get('daily', {})
            return {
                'temp': round(current.get('temperature_2m', 0)),
                'humidity': round(current.get('relative_humidity_2m', 0)),
                'code': current.get('weather_code', 0),
                'high': round(daily.get('temperature_2m_max', [0])[0]),
                'low': round(daily.get('temperature_2m_min', [0])[0]),
            }
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Drawing helpers
    # -------------------------------------------------------------------------

    def _draw_cloud(self, draw, cx, cy, color=(200, 205, 220)):
        """Large rounded cloud centered at (cx, cy). Spans ~30px wide, ~16px tall."""
        draw.ellipse([cx - 14, cy - 3, cx + 14, cy + 8], fill=color)   # main body
        draw.ellipse([cx - 16, cy - 9,  cx - 2,  cy + 4], fill=color)  # left bump
        draw.ellipse([cx - 8,  cy - 13, cx + 8,  cy + 2], fill=color)  # center bump (tallest)
        draw.ellipse([cx + 2,  cy - 9,  cx + 16, cy + 4], fill=color)  # right bump

    def _draw_sun(self, draw, cx, cy, radius=8, ray_offset=0.0,
                  body_color=(255, 200, 0), ray_color=(255, 220, 50)):
        """Sun circle with 8 rotating rays."""
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=body_color)
        for i in range(8):
            angle = ray_offset + math.radians(i * 45)
            x1 = cx + int((radius + 2) * math.cos(angle))
            y1 = cy + int((radius + 2) * math.sin(angle))
            x2 = cx + int((radius + 5) * math.cos(angle))
            y2 = cy + int((radius + 5) * math.sin(angle))
            draw.line([(x1, y1), (x2, y2)], fill=ray_color, width=1)

    def _draw_labels(self, draw, temp, font):
        """Day abbreviation bottom-left, temperature bottom-right."""
        day = datetime.now().strftime('%a').upper()
        draw.text((2, 22), day, fill=(255, 255, 255), font=font)

        temp_str = f"{temp}\u00b0"
        try:
            tw = int(draw.textlength(temp_str, font=font))
        except Exception:
            tw = len(temp_str) * 5
        draw.text((62 - tw, 22), temp_str, fill=(255, 255, 255), font=font)

    # -------------------------------------------------------------------------
    # Per-condition animations (20 frames each, except thunderstorm = 12)
    # -------------------------------------------------------------------------

    def _frames_clear(self, temp, font) -> List[Image.Image]:
        """Large sun centered, rays rotate."""
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 12))
            draw = ImageDraw.Draw(img)
            self._draw_sun(draw, 32, 12, radius=9,
                           ray_offset=math.radians(f * 18))
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_partly_cloudy(self, temp, font) -> List[Image.Image]:
        """Sun upper-right with rotating rays; large cloud left-center (like screenshot)."""
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 12))
            draw = ImageDraw.Draw(img)
            # Sun behind/beside cloud (upper right)
            self._draw_sun(draw, 44, 10, radius=7,
                           ray_offset=math.radians(f * 18))
            # Cloud overlaps sun from the left
            self._draw_cloud(draw, 24, 15)
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_cloudy(self, temp, font) -> List[Image.Image]:
        """Large grey cloud with gentle breathing drift."""
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 12))
            draw = ImageDraw.Draw(img)
            drift = int(math.sin(f * math.pi / 10) * 2)
            self._draw_cloud(draw, 32 + drift, 13, color=(150, 155, 170))
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_rain(self, temp, font) -> List[Image.Image]:
        """Dark cloud with animated blue rain drops falling."""
        drops = [(6, 0), (16, 4), (26, 1), (36, 5), (46, 0), (56, 3),
                 (11, 9), (21, 7), (31, 10), (41, 7), (51, 9)]
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 18))
            draw = ImageDraw.Draw(img)
            self._draw_cloud(draw, 30, 8, color=(110, 115, 135))
            for bx, by in drops:
                y = (by + f * 2) % 20 + 13
                draw.line([(bx, y), (bx - 1, y + 3)], fill=(70, 120, 255), width=1)
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_snow(self, temp, font) -> List[Image.Image]:
        """Cloud with falling white snowflake asterisks."""
        flakes = [(6, 0), (18, 4), (30, 1), (42, 5), (54, 0),
                  (12, 9), (24, 7), (36, 10), (48, 8)]
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 18))
            draw = ImageDraw.Draw(img)
            self._draw_cloud(draw, 30, 8, color=(160, 165, 185))
            for bx, by in flakes:
                y = (by + f) % 18 + 13
                x = (bx + f // 4) % 62
                if y > 13:
                    for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0),
                                   (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                        draw.point((x + dx, y + dy), fill=(170, 170, 210))
                    draw.point((x, y), fill=(240, 240, 255))
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_thunderstorm(self, temp, font) -> List[Image.Image]:
        """Dark sky, dark cloud, flashing yellow lightning bolt."""
        bolt = [(32, 12), (27, 20), (31, 20), (25, 29)]
        frames = []
        for f in range(12):
            flash = f % 4 in (0, 1)
            bg = (4, 4, 18) if not flash else (18, 18, 50)
            img = Image.new('RGB', (64, 32), bg)
            draw = ImageDraw.Draw(img)
            self._draw_cloud(draw, 30, 8, color=(70, 70, 90))
            if flash:
                for i in range(len(bolt) - 1):
                    draw.line([bolt[i], bolt[i + 1]], fill=(255, 255, 60), width=2)
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_fog(self, temp, font) -> List[Image.Image]:
        """Slowly scrolling horizontal fog bands."""
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (4, 4, 10))
            draw = ImageDraw.Draw(img)
            offset = f % 5
            for row in range(5):
                y = (row * 5 + offset) % 23 + 1
                br = 80 + row * 18
                draw.line([(3, y), (60, y)], fill=(br, br, br + 12))
                if y + 1 < 23:
                    draw.line([(3, y + 1), (60, y + 1)],
                              fill=(br // 2, br // 2, br // 2 + 6))
            self._draw_labels(draw, temp, font)
            frames.append(img)
        return frames

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------

    def get_frames(self) -> List[Image.Image]:
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 8)
        except Exception:
            font = ImageFont.load_default()

        weather = self._fetch_weather()
        if not weather:
            img = Image.new('RGB', (64, 32), (20, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 10), "No weather", fill=(255, 80, 80), font=font)
            return [img] * 20

        code = weather['code']
        temp = weather['temp']

        if code <= 1:
            frames = self._frames_clear(temp, font)
        elif code == 2:
            frames = self._frames_partly_cloudy(temp, font)
        elif code == 3:
            frames = self._frames_cloudy(temp, font)
        elif code in (45, 48):
            frames = self._frames_fog(temp, font)
        elif (51 <= code <= 67) or (80 <= code <= 82):
            frames = self._frames_rain(temp, font)
        elif (71 <= code <= 77) or code in (85, 86):
            frames = self._frames_snow(temp, font)
        elif 95 <= code <= 99:
            frames = self._frames_thunderstorm(temp, font)
        else:
            frames = self._frames_cloudy(temp, font)

        return frames

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 600
