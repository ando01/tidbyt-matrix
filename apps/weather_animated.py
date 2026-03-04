"""Animated weather app with pixel art animations per condition"""

import time
import math
import requests
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class WeatherAnimatedApp(MatrixApp):
    """Weather display with pixel art animations based on WMO weather codes"""

    WMO_CODES = {
        0: "Clear", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy Fog",
        51: "Lt Drizzle", 53: "Drizzle", 55: "Hvy Drizzle",
        61: "Lt Rain", 63: "Rain", 65: "Hvy Rain",
        71: "Lt Snow", 73: "Snow", 75: "Hvy Snow", 77: "Snow Grains",
        80: "Showers", 81: "Showers", 82: "Hvy Showers",
        85: "Snow Showers", 86: "Hvy Snow",
        95: "Thunderstorm", 96: "Thunderstorm", 99: "Hvy Storm",
    }

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("WeatherAnim", config)
        self.zip_code = config.config.get('zip_code', '02134') if config else '02134'
        self.lat = None
        self.lon = None
        self.location_name = self.zip_code
        self._resolve_location()

    def _resolve_location(self):
        try:
            url = f"https://api.zippopotam.us/us/{self.zip_code}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                place = data['places'][0]
                self.lat = float(place['latitude'])
                self.lon = float(place['longitude'])
                self.location_name = place['place name']
                return
        except Exception:
            pass
        try:
            url = (f"https://geocoding-api.open-meteo.com/v1/search"
                   f"?name={self.zip_code}&count=1&country=US&language=en&format=json")
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get('results'):
                result = data['results'][0]
                self.lat = result['latitude']
                self.lon = result['longitude']
                self.location_name = result.get('name', self.zip_code)
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
                f"&current=temperature_2m,weather_code"
                f"&temperature_unit=fahrenheit&timezone=auto&forecast_days=1"
            )
            resp = requests.get(url, timeout=5)
            data = resp.json()
            current = data.get('current', {})
            return {
                'temp': round(current.get('temperature_2m', 0)),
                'code': current.get('weather_code', 0),
            }
        except Exception as e:
            print(f"WeatherAnim fetch error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Animation helpers
    # -------------------------------------------------------------------------

    def _draw_temp(self, draw, temp, font):
        """Draw temperature string in bottom-left corner."""
        draw.text((2, 22), f"{temp}°F", fill=(220, 220, 220), font=font)

    def _frames_clear(self, temp, font) -> List[Image.Image]:
        """Sunny: animated rotating rays around a central sun."""
        frames = []
        cx, cy, r = 48, 10, 4
        ray_len = 5
        num_rays = 8
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 20))
            draw = ImageDraw.Draw(img)
            # Sun body
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 0))
            # Rotating rays
            angle_offset = math.radians(f * (360 / 20))
            for i in range(num_rays):
                angle = angle_offset + math.radians(i * (360 / num_rays))
                x1 = cx + int((r + 2) * math.cos(angle))
                y1 = cy + int((r + 2) * math.sin(angle))
                x2 = cx + int((r + ray_len) * math.cos(angle))
                y2 = cy + int((r + ray_len) * math.sin(angle))
                draw.line([(x1, y1), (x2, y2)], fill=(255, 200, 0), width=1)
            self._draw_temp(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_cloudy(self, temp, font) -> List[Image.Image]:
        """Cloudy: clouds drifting left."""
        frames = []
        cloud_positions = [(10, 5), (35, 10), (55, 4)]
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 15))
            draw = ImageDraw.Draw(img)
            for base_x, base_y in cloud_positions:
                x = (base_x - f) % 70 - 5
                for dx, dy, rx, ry in [(0, 4, 6, 4), (6, 2, 5, 3), (-5, 2, 5, 3)]:
                    draw.ellipse([x + dx - rx, base_y + dy - ry,
                                  x + dx + rx, base_y + dy + ry],
                                 fill=(160, 160, 175))
            self._draw_temp(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_rain(self, temp, font) -> List[Image.Image]:
        """Rain: blue drops falling diagonally."""
        frames = []
        drops = [(5, 0), (15, 5), (25, 2), (35, 8), (45, 1), (55, 6),
                 (10, 15), (30, 12), (50, 18)]
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 25))
            draw = ImageDraw.Draw(img)
            for bx, by in drops:
                x = (bx + f) % 64
                y = (by + f * 2) % 32
                draw.line([(x, y), (x - 1, y + 3)], fill=(80, 130, 255), width=1)
            self._draw_temp(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_snow(self, temp, font) -> List[Image.Image]:
        """Snow: white asterisk flakes drifting."""
        frames = []
        flakes = [(8, 3), (20, 0), (35, 6), (50, 2), (15, 14),
                  (42, 10), (58, 16), (3, 20), (28, 18)]
        for f in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 20))
            draw = ImageDraw.Draw(img)
            for bx, by in flakes:
                x = (bx + f // 3) % 64
                y = (by + f) % 32
                for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0),
                               (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                    draw.point((x + dx, y + dy), fill=(220, 220, 255))
                draw.point((x, y), fill=(255, 255, 255))
            self._draw_temp(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_thunderstorm(self, temp, font) -> List[Image.Image]:
        """Thunderstorm: dark sky, flashing lightning bolt."""
        bolt = [(32, 4), (28, 14), (32, 14), (26, 28)]
        frames = []
        for f in range(10):
            flash = (f % 3 == 0)
            bg = (5, 5, 20) if not flash else (30, 30, 60)
            img = Image.new('RGB', (64, 32), bg)
            draw = ImageDraw.Draw(img)
            if flash:
                bolt_color = (255, 255, 100)
                for i in range(len(bolt) - 1):
                    draw.line([bolt[i], bolt[i + 1]], fill=bolt_color, width=2)
            self._draw_temp(draw, temp, font)
            frames.append(img)
        return frames

    def _frames_fog(self, temp, font) -> List[Image.Image]:
        """Fog: slow scrolling horizontal grey lines."""
        frames = []
        for f in range(20):
            img = Image.new('RGB', (64, 32), (10, 10, 15))
            draw = ImageDraw.Draw(img)
            offset = f % 4
            for y in range(offset, 32, 5):
                brightness = 100 + (y * 2) % 50
                draw.line([(0, y), (63, y)], fill=(brightness, brightness, brightness + 10))
            self._draw_temp(draw, temp, font)
            frames.append(img)
        return frames

    def get_frames(self) -> List[Image.Image]:
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
        except Exception:
            font = ImageFont.load_default()

        weather = self._fetch_weather()
        if not weather:
            img = Image.new('RGB', (64, 32), (20, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 10), "No weather", fill=(255, 100, 100), font=font)
            return [img] * 20

        code = weather['code']
        temp = weather['temp']

        if code <= 1:
            return self._frames_clear(temp, font)
        elif code <= 3:
            return self._frames_cloudy(temp, font)
        elif code in (45, 48):
            return self._frames_fog(temp, font)
        elif (51 <= code <= 67) or (80 <= code <= 82):
            return self._frames_rain(temp, font)
        elif (71 <= code <= 77) or code in (85, 86):
            return self._frames_snow(temp, font)
        elif 95 <= code <= 99:
            return self._frames_thunderstorm(temp, font)
        else:
            return self._frames_cloudy(temp, font)

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 600
