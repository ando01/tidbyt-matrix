#!/usr/bin/env python3
"""
App Framework for Tidbyt-like Matrix Display
Provides base class and utilities for building apps
"""

import time
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
import requests


@dataclass
class AppConfig:
    """Configuration for an app"""
    enabled: bool = True
    refresh_interval: int = 300  # Refresh every 5 minutes
    display_duration: int = 10  # Show for 10 seconds
    priority: int = 0  # Higher priority shows first
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class MatrixApp(ABC):
    """Base class for matrix display apps"""
    
    def __init__(self, name: str, config: Optional[AppConfig] = None):
        self.name = name
        self.config = config or AppConfig()
        self.last_refresh = 0
        self.cached_frames = []
        
    @abstractmethod
    def get_frames(self) -> List[Image.Image]:
        """
        Return list of PIL Images to display.
        Each frame is displayed for ~0.1 seconds
        """
        pass
    
    @abstractmethod
    def needs_refresh(self) -> bool:
        """Check if cached data needs refresh"""
        pass
    
    def get_display_duration(self) -> int:
        """Get how long this app should display (seconds)"""
        return self.config.display_duration
    
    def is_enabled(self) -> bool:
        """Check if app is enabled"""
        return self.config.enabled
    
    def refresh(self):
        """Update app data if needed"""
        if self.needs_refresh():
            self.cached_frames = self.get_frames()
            self.last_refresh = time.time()
    
    def get_cached_frames(self) -> List[Image.Image]:
        """Get cached frames"""
        return self.cached_frames


# ============================================================================
# EXAMPLE APPS
# ============================================================================

class ClockApp(MatrixApp):
    """Simple digital clock"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Clock", config)
        self.font_size = 6
        
    def get_frames(self) -> List[Image.Image]:
        frames = []
        # 4 frames at 2fps = 2 seconds, colon blinks each second
        for i in range(4):
            now = datetime.now()
            hour = now.strftime("%H")
            minute = now.strftime("%M")

            # Alternate colon every second
            if (i // 20) % 2 == 0:
                display_text = f"{hour}:{minute}"
            else:
                display_text = f"{hour} {minute}"

            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), display_text, font=font)
            x = (64 - (bbox[2] - bbox[0])) // 2
            y = (32 - (bbox[3] - bbox[1])) // 2
            draw.text((x, y), display_text, fill=(255, 255, 255), font=font)
            frames.append(img)

        return frames
    
    def needs_refresh(self) -> bool:
        # Refresh every 10 seconds
        return time.time() - self.last_refresh > 10


class WeatherApp(MatrixApp):
    """Weather display using Open-Meteo API (free, no key required)"""

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
        super().__init__("Weather", config)
        self.zip_code = config.config.get('zip_code', '02134') if config else '02134'
        self.lat = None
        self.lon = None
        self.location_name = self.zip_code
        self._resolve_location()

    def _resolve_location(self):
        """Convert zip code to lat/lon using Open-Meteo geocoding"""
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.zip_code}&count=1&country=US&language=en&format=json"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get('results'):
                result = data['results'][0]
                self.lat = result['latitude']
                self.lon = result['longitude']
                self.location_name = result.get('name', self.zip_code)
        except Exception as e:
            print(f"Weather: Could not resolve location for {self.zip_code}: {e}")

    def _fetch_weather(self):
        """Fetch current conditions + today's high/low from Open-Meteo"""
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
            resp = requests.get(url, timeout=5)
            data = resp.json()
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

    def get_frames(self) -> List[Image.Image]:
        frames = []
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
            data_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
            med_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 13)
        except:
            title_font = data_font = med_font = ImageFont.load_default()

        weather = self._fetch_weather()

        if not weather:
            img = Image.new('RGB', (64, 32), (20, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 10), "No weather", fill=(255, 100, 100), font=title_font)
            return [img] * 6

        condition = self.WMO_CODES.get(weather['code'], "Unknown")

        # Slide 1: Location + Temperature
        img = Image.new('RGB', (64, 32), (0, 0, 15))
        draw = ImageDraw.Draw(img)
        draw.text((2, 1), self.location_name[:10], fill=(255, 200, 0), font=title_font)
        draw.text((2, 13), f"{weather['temp']}°F", fill=(100, 200, 255), font=data_font)
        frames.extend([img] * 6)

        # Slide 2: Condition + Humidity
        img = Image.new('RGB', (64, 32), (0, 0, 15))
        draw = ImageDraw.Draw(img)
        draw.text((2, 1), condition[:12], fill=(150, 200, 255), font=title_font)
        draw.text((2, 16), f"Humidity {weather['humidity']}%", fill=(150, 150, 200), font=title_font)
        frames.extend([img] * 6)

        # Slide 3: High / Low
        img = Image.new('RGB', (64, 32), (0, 0, 15))
        draw = ImageDraw.Draw(img)
        draw.text((2, 1), "Today", fill=(255, 200, 0), font=title_font)
        draw.text((2, 13), f"H:{weather['high']} L:{weather['low']}", fill=(200, 200, 100), font=med_font)
        frames.extend([img] * 6)

        return frames

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 600


class StockApp(MatrixApp):
    """Stock ticker using yfinance"""

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Stocks", config)
        self.symbols = config.config.get('symbols', ['AAPL', 'TSLA']) if config else ['AAPL', 'TSLA']

    def _fetch_stocks(self):
        """Fetch real stock data using yfinance"""
        results = []
        try:
            import yfinance as yf
            for sym in self.symbols:
                try:
                    info = yf.Ticker(sym).fast_info
                    price = info.last_price
                    prev = info.previous_close
                    if price and prev:
                        pct = (price - prev) / prev * 100
                        is_up = price >= prev
                        results.append({
                            'symbol': sym,
                            'price': f"{price:.2f}",
                            'change': f"{'+' if is_up else ''}{pct:.1f}%",
                            'is_up': is_up,
                        })
                except Exception as e:
                    print(f"Stock error for {sym}: {e}")
        except ImportError:
            print("yfinance not installed — run: sudo pip install --break-system-packages yfinance")
            for sym in self.symbols:
                results.append({'symbol': sym, 'price': 'N/A', 'change': '+0.0%', 'is_up': True})
        return results

    def get_frames(self) -> List[Image.Image]:
        frames = []
        try:
            symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
            price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
        except:
            symbol_font = price_font = ImageFont.load_default()

        stocks = self._fetch_stocks()

        if not stocks:
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 10), "No data", fill=(255, 100, 100), font=price_font)
            return [img] * 6

        for stock in stocks:
            color = (100, 255, 100) if stock['is_up'] else (255, 100, 100)
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 2), stock['symbol'], fill=(255, 255, 255), font=symbol_font)
            draw.text((2, 18), stock['price'], fill=(200, 200, 200), font=price_font)
            draw.text((36, 18), stock['change'], fill=color, font=price_font)
            frames.extend([img] * 6)

        return frames

    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 300


class ArtApp(MatrixApp):
    """Animated art/patterns"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Art", config)
    
    def get_frames(self) -> List[Image.Image]:
        frames = []
        
        # Generate simple animated pattern
        for frame_num in range(20):
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw animated checkerboard
            for x in range(0, 64, 4):
                for y in range(0, 32, 4):
                    offset = (frame_num + (x + y) // 8) % 2
                    if offset == 0:
                        draw.rectangle([x, y, x+3, y+3], fill=(255, 100, 150))
                    else:
                        draw.rectangle([x, y, x+3, y+3], fill=(50, 100, 255))

            frames.append(img)
        
        return frames
    
    def needs_refresh(self) -> bool:
        return False  # Patterns don't need refresh


class NewsHeadlinesApp(MatrixApp):
    """Scrolling news headlines"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("News", config)
    
    def get_frames(self) -> List[Image.Image]:
        frames = []
        
        # Mock headlines
        headlines = [
            "Red Sox win 5-2",
            "Breaking News Alert",
            "Markets up today",
        ]
        
        for headline in headlines:
            # Create scrolling text frames
            for scroll_pos in range(64, -len(headline)*8, -2):
                img = Image.new('RGB', (64, 32), (0, 0, 0))
                draw = ImageDraw.Draw(img)

                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
                except:
                    font = ImageFont.load_default()

                draw.text((scroll_pos, 10), headline, fill=(255, 200, 100), font=font)
                frames.append(img)
        
        return frames
    
    def needs_refresh(self) -> bool:
        return time.time() - self.last_refresh > 1800  # 30 minutes


class AppManager:
    """Manage and cycle through apps"""
    
    def __init__(self):
        self.apps: List[MatrixApp] = []
        self.current_app_index = 0
        self.app_start_time = time.time()
    
    def add_app(self, app: MatrixApp):
        """Add an app to the manager"""
        self.apps.append(app)
        # Sort by priority (higher first)
        self.apps.sort(key=lambda a: a.config.priority, reverse=True)
    
    def get_enabled_apps(self) -> List[MatrixApp]:
        """Get list of enabled apps"""
        return [app for app in self.apps if app.is_enabled()]
    
    def get_next_app(self) -> Optional[MatrixApp]:
        """Get next app to display"""
        enabled = self.get_enabled_apps()
        if not enabled:
            return None
        
        self.current_app_index = (self.current_app_index + 1) % len(enabled)
        return enabled[self.current_app_index]
    
    def get_current_app(self) -> Optional[MatrixApp]:
        """Get currently active app"""
        enabled = self.get_enabled_apps()
        if not enabled:
            return None
        self.current_app_index = self.current_app_index % len(enabled)
        return enabled[self.current_app_index]
    
    def should_rotate(self) -> bool:
        """Check if we should rotate to next app"""
        current = self.get_current_app()
        if not current:
            return True
        
        elapsed = time.time() - self.app_start_time
        return elapsed >= current.get_display_duration()
    
    def rotate_app(self):
        """Rotate to next app"""
        self.app_start_time = time.time()
        self.get_next_app()


# Example usage
if __name__ == "__main__":
    manager = AppManager()
    
    # Add apps
    manager.add_app(ClockApp())
    manager.add_app(WeatherApp())
    manager.add_app(StockApp())
    manager.add_app(ArtApp())
    
    print(f"Loaded {len(manager.apps)} apps")
    for app in manager.apps:
        print(f"  - {app.name}")
