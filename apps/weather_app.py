"""Combined weather app — static conditions + 3-day forecast with scroll transition."""

import time
import math
import requests
from datetime import datetime
from PIL import Image, ImageDraw
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


# 3×5 pixel font — 3px wide chars, 1px gap → 4px advance per char, 5px tall
_FONT = {
    ' ': (0, 0, 0, 0, 0),
    '-': (0, 0, 7, 0, 0),
    '/': (1, 1, 2, 4, 4),
    '°': (2, 5, 2, 0, 0),
    '0': (7, 5, 5, 5, 7), '1': (2, 6, 2, 2, 7), '2': (7, 1, 7, 4, 7),
    '3': (7, 1, 3, 1, 7), '4': (5, 5, 7, 1, 1), '5': (7, 4, 7, 1, 7),
    '6': (7, 4, 7, 5, 7), '7': (7, 1, 2, 2, 2), '8': (7, 5, 7, 5, 7),
    '9': (7, 5, 7, 1, 7),
    'A': (2, 5, 7, 5, 5), 'B': (6, 5, 6, 5, 6), 'C': (3, 4, 4, 4, 3),
    'D': (6, 5, 5, 5, 6), 'E': (7, 4, 6, 4, 7), 'F': (7, 4, 6, 4, 4),
    'G': (3, 4, 5, 5, 3), 'H': (5, 5, 7, 5, 5), 'I': (7, 2, 2, 2, 7),
    'J': (3, 1, 1, 5, 2), 'K': (5, 5, 6, 5, 5), 'L': (4, 4, 4, 4, 7),
    'M': (5, 7, 5, 5, 5), 'N': (5, 5, 5, 5, 5), 'O': (2, 5, 5, 5, 2),
    'P': (6, 5, 6, 4, 4), 'Q': (2, 5, 5, 3, 1), 'R': (6, 5, 6, 5, 5),
    'S': (3, 4, 2, 1, 6), 'T': (7, 2, 2, 2, 2), 'U': (5, 5, 5, 5, 7),
    'V': (5, 5, 5, 2, 2), 'W': (5, 5, 5, 7, 2), 'X': (5, 5, 2, 5, 5),
    'Y': (5, 5, 2, 2, 2), 'Z': (7, 1, 2, 4, 7),
}


def _px(draw, text: str, x: int, y: int, color: tuple) -> int:
    """Draw text with 3×5 pixel font. Returns x position after last char."""
    cx = x
    for ch in str(text).upper():
        rows = _FONT.get(ch)
        if rows is None:
            cx += 4
            continue
        for ri, row in enumerate(rows):
            for ci in range(3):
                if row & (4 >> ci):
                    draw.point((cx + ci, y + ri), fill=color)
        cx += 4
    return cx


def _pw(text: str) -> int:
    """Pixel width of text in 3×5 font."""
    return len(str(text)) * 4


class WeatherApp(MatrixApp):
    """Static weather icon + day/temp labels; scrolls to 3-day forecast."""

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
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
                f"&temperature_unit=fahrenheit&timezone=auto&forecast_days=4"
            )
            data = requests.get(url, timeout=5).json()
            current = data.get('current', {})
            daily = data.get('daily', {})
            times = daily.get('time', [])
            codes = daily.get('weather_code', [])
            highs = daily.get('temperature_2m_max', [])
            lows  = daily.get('temperature_2m_min', [])
            forecast = []
            for i in range(1, 4):
                if i < len(times):
                    forecast.append({
                        'day':  datetime.strptime(times[i], '%Y-%m-%d').strftime('%a').upper(),
                        'code': codes[i] if i < len(codes) else 0,
                        'high': round(highs[i]) if i < len(highs) else 0,
                        'low':  round(lows[i])  if i < len(lows)  else 0,
                    })
            return {
                'temp':     round(current.get('temperature_2m', 0)),
                'humidity': round(current.get('relative_humidity_2m', 0)),
                'code':     current.get('weather_code', 0),
                'high':     round(highs[0]) if highs else 0,
                'low':      round(lows[0])  if lows  else 0,
                'forecast': forecast,
            }
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Large icon drawing (for current conditions screen)
    # -------------------------------------------------------------------------

    def _draw_cloud(self, draw, cx, cy, color=(200, 205, 220)):
        draw.ellipse([cx - 14, cy - 3,  cx + 14, cy + 8], fill=color)
        draw.ellipse([cx - 16, cy - 9,  cx - 2,  cy + 4], fill=color)
        draw.ellipse([cx - 8,  cy - 13, cx + 8,  cy + 2], fill=color)
        draw.ellipse([cx + 2,  cy - 9,  cx + 16, cy + 4], fill=color)

    def _draw_sun(self, draw, cx, cy, radius=8, color=(255, 200, 0)):
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
        for i in range(8):
            angle = math.radians(i * 45 + 22.5)
            x1 = cx + int((radius + 2) * math.cos(angle))
            y1 = cy + int((radius + 2) * math.sin(angle))
            x2 = cx + int((radius + 5) * math.cos(angle))
            y2 = cy + int((radius + 5) * math.sin(angle))
            draw.line([(x1, y1), (x2, y2)], fill=(255, 220, 50), width=1)

    def _draw_large_icon(self, draw, code):
        """Draw the large static weather icon for the conditions screen."""
        if code <= 1:
            self._draw_sun(draw, 32, 11, radius=9)
        elif code == 2:
            self._draw_sun(draw, 44, 10, radius=7)
            self._draw_cloud(draw, 24, 15)
        elif code == 3:
            self._draw_cloud(draw, 32, 13, color=(150, 155, 170))
        elif code in (45, 48):
            for row, y in enumerate(range(4, 22, 4)):
                br = 80 + row * 18
                draw.line([(4, y), (60, y)], fill=(br, br, br + 12))
        elif (51 <= code <= 67) or (80 <= code <= 82):
            self._draw_cloud(draw, 30, 8, color=(110, 115, 135))
            for x, y0 in [(8, 14), (18, 16), (28, 14), (38, 16), (48, 14), (58, 16)]:
                draw.line([(x, y0), (x - 1, y0 + 4)], fill=(70, 120, 255), width=1)
        elif (71 <= code <= 77) or code in (85, 86):
            self._draw_cloud(draw, 30, 8, color=(160, 165, 185))
            for x, y0 in [(8, 15), (18, 17), (28, 15), (38, 17), (48, 15), (56, 17)]:
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    draw.point((x + dx, y0 + dy), fill=(180, 180, 220))
                draw.point((x, y0), fill=(240, 240, 255))
        elif 95 <= code <= 99:
            self._draw_cloud(draw, 30, 8, color=(70, 70, 90))
            bolt = [(32, 12), (27, 20), (31, 20), (25, 28)]
            for i in range(len(bolt) - 1):
                draw.line([bolt[i], bolt[i + 1]], fill=(255, 255, 60), width=2)
        else:
            self._draw_cloud(draw, 32, 13, color=(150, 155, 170))

    # -------------------------------------------------------------------------
    # Small icon drawing (for forecast columns)
    # -------------------------------------------------------------------------

    def _draw_mini_icon(self, draw, cx, cy, code):
        """Small ~12×10px icon centered at (cx, cy)."""
        if code <= 1:
            draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 200, 0))
            for deg in range(0, 360, 45):
                a = math.radians(deg)
                draw.point((cx + int(5 * math.cos(a)), cy + int(5 * math.sin(a))),
                           fill=(255, 220, 50))
        elif code == 2:
            draw.ellipse([cx + 1, cy - 4, cx + 5, cy],    fill=(255, 200, 0))
            draw.point((cx + 6, cy - 2), fill=(255, 220, 50))
            draw.point((cx + 3, cy - 5), fill=(255, 220, 50))
            draw.ellipse([cx - 6, cy - 1, cx + 3, cy + 4], fill=(190, 195, 210))
            draw.ellipse([cx - 4, cy - 4, cx,     cy + 1], fill=(190, 195, 210))
            draw.ellipse([cx - 1, cy - 3, cx + 3, cy + 1], fill=(190, 195, 210))
        elif code == 3:
            draw.ellipse([cx - 6, cy - 1, cx + 6, cy + 4], fill=(150, 155, 170))
            draw.ellipse([cx - 4, cy - 4, cx,     cy + 1], fill=(150, 155, 170))
            draw.ellipse([cx,     cy - 3, cx + 5, cy + 1], fill=(150, 155, 170))
        elif code in (45, 48):
            for dy in (-2, 0, 2):
                draw.line([(cx - 5, cy + dy), (cx + 5, cy + dy)], fill=(130, 130, 145))
        elif (51 <= code <= 67) or (80 <= code <= 82):
            draw.ellipse([cx - 5, cy - 3, cx + 5, cy + 1], fill=(110, 115, 135))
            draw.ellipse([cx - 3, cy - 6, cx + 1, cy - 1], fill=(110, 115, 135))
            draw.ellipse([cx + 1, cy - 5, cx + 5, cy - 1], fill=(110, 115, 135))
            draw.line([(cx - 2, cy + 2), (cx - 3, cy + 5)], fill=(70, 120, 255))
            draw.line([(cx + 2, cy + 2), (cx + 1, cy + 5)], fill=(70, 120, 255))
        elif (71 <= code <= 77) or code in (85, 86):
            draw.ellipse([cx - 5, cy - 3, cx + 5, cy + 1], fill=(160, 165, 185))
            draw.ellipse([cx - 3, cy - 6, cx + 1, cy - 1], fill=(160, 165, 185))
            draw.ellipse([cx + 1, cy - 5, cx + 5, cy - 1], fill=(160, 165, 185))
            for sx in (cx - 3, cx, cx + 3):
                draw.point((sx, cy + 4), fill=(210, 210, 255))
        elif 95 <= code <= 99:
            draw.ellipse([cx - 5, cy - 3, cx + 5, cy + 1], fill=(70, 70, 90))
            draw.ellipse([cx - 3, cy - 6, cx + 1, cy - 1], fill=(70, 70, 90))
            draw.ellipse([cx + 1, cy - 5, cx + 5, cy - 1], fill=(70, 70, 90))
            draw.line([(cx,     cy + 2), (cx - 2, cy + 5)], fill=(255, 255, 60))
            draw.line([(cx - 2, cy + 5), (cx,     cy + 5)], fill=(255, 255, 60))
            draw.line([(cx,     cy + 5), (cx - 2, cy + 8)], fill=(255, 255, 60))
        else:
            draw.ellipse([cx - 5, cy - 2, cx + 5, cy + 3], fill=(150, 155, 170))
            draw.ellipse([cx - 3, cy - 5, cx + 1, cy],     fill=(150, 155, 170))

    # -------------------------------------------------------------------------
    # Frame builders
    # -------------------------------------------------------------------------

    def _make_conditions_frame(self, weather) -> Image.Image:
        """Static current-conditions frame: large icon + day bottom-left + H/L bottom-right."""
        img = Image.new('RGB', (64, 32), (0, 0, 12))
        draw = ImageDraw.Draw(img)

        self._draw_large_icon(draw, weather['code'])

        # Day abbreviation — bottom left
        day = datetime.now().strftime('%a').upper()
        _px(draw, day, 2, 26, (220, 220, 220))

        # High / Low — bottom right, right-aligned
        hi_str = f"H{weather['high']}"
        lo_str = f"L{weather['low']}"
        total_w = _pw(hi_str) + _pw(' ') + _pw(lo_str)
        x = 62 - total_w
        x = _px(draw, hi_str, x, 26, (255, 160, 60))
        x = _px(draw, ' ',    x, 26, (220, 220, 220))
        _px(draw, lo_str, x, 26, (80, 180, 255))

        return img

    def _make_forecast_frame(self, forecast) -> Image.Image:
        """3-column forecast: day name, mini icon, H° and L° per column."""
        img = Image.new('RGB', (64, 32), (0, 0, 12))
        draw = ImageDraw.Draw(img)

        # Subtle column dividers
        draw.line([(21, 3), (21, 28)], fill=(35, 35, 55))
        draw.line([(42, 3), (42, 28)], fill=(35, 35, 55))

        col_centers = [11, 32, 53]

        for i, day_data in enumerate(forecast[:3]):
            cx = col_centers[i]

            # Day name — centered in column
            label = day_data['day'][:3]
            lx = cx - _pw(label) // 2
            _px(draw, label, lx, 2, (200, 200, 200))

            # Mini icon centered in column
            self._draw_mini_icon(draw, cx, 14, day_data['code'])

            # High temp (orange) — centered
            hi_str = f"H{day_data['high']}"
            _px(draw, hi_str, cx - _pw(hi_str) // 2, 21, (255, 160, 60))

            # Low temp (cyan) — centered
            lo_str = f"L{day_data['low']}"
            _px(draw, lo_str, cx - _pw(lo_str) // 2, 27, (80, 180, 255))

        return img

    def _scroll_transition(self, frame_a: Image.Image, frame_b: Image.Image,
                           steps: int = 8) -> List[Image.Image]:
        """Slide frame_a out left while frame_b enters from the right."""
        frames = []
        for i in range(1, steps + 1):
            offset = (64 * i) // steps
            combined = Image.new('RGB', (64, 32), (0, 0, 0))
            combined.paste(frame_a, (-offset, 0))
            combined.paste(frame_b, (64 - offset, 0))
            frames.append(combined)
        return frames

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------

    def get_frames(self) -> List[Image.Image]:
        weather = self._fetch_weather()
        if not weather:
            img = Image.new('RGB', (64, 32), (20, 0, 0))
            draw = ImageDraw.Draw(img)
            _px(draw, "NO WEATHER", 2, 13, (255, 80, 80))
            return [img] * 20

        cond_frame = self._make_conditions_frame(weather)

        forecast = weather.get('forecast', [])
        if not forecast:
            return [cond_frame] * 20

        fcast_frame = self._make_forecast_frame(forecast)

        transition = self._scroll_transition(cond_frame, fcast_frame, steps=8)

        # Equal display time: 20 frames each at 2fps = 10s each
        return [cond_frame] * 20 + transition + [fcast_frame] * 20

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 600
