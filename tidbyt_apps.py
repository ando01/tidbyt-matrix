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
        # Generate 60 frames (6 seconds of animation)
        for i in range(60):
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
    """Weather display (mock data)"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Weather", config)
        self.api_key = config.config.get('api_key', '') if config else ''
        self.location = config.config.get('location', 'Boston, MA') if config else 'Boston, MA'
    
    def get_frames(self) -> List[Image.Image]:
        frames = []

        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
            data_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
        except:
            title_font = data_font = ImageFont.load_default()

        # Frame 1: Temperature
        img = Image.new('RGB', (64, 32), (0, 0, 10))
        draw = ImageDraw.Draw(img)
        draw.text((2, 2), "WEATHER", fill=(255, 200, 0), font=title_font)
        draw.text((8, 15), "72°F", fill=(100, 200, 255), font=data_font)
        frames.append(img)

        # Frame 2: Condition
        img = Image.new('RGB', (64, 32), (0, 0, 10))
        draw = ImageDraw.Draw(img)
        draw.text((2, 2), "WEATHER", fill=(255, 200, 0), font=title_font)
        draw.text((2, 17), "Partly Cloudy", fill=(150, 150, 200), font=title_font)
        frames.append(img)

        return frames
    
    def needs_refresh(self) -> bool:
        # Refresh every 10 minutes
        return time.time() - self.last_refresh > 600


class StockApp(MatrixApp):
    """Stock ticker (mock data)"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Stocks", config)
        self.symbols = config.config.get('symbols', ['AAPL', 'TSLA']) if config else ['AAPL', 'TSLA']
    
    def get_frames(self) -> List[Image.Image]:
        frames = []
        
        # Mock stock data
        stocks = {
            'AAPL': ('180.5', '+2.3%', True),
            'TSLA': ('245.0', '-1.2%', False),
        }
        
        for symbol in self.symbols:
            price, change, is_up = stocks.get(symbol, ('0.0', '+0.0%', True))
            color = (100, 255, 100) if is_up else (255, 100, 100)

            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            try:
                symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
                price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
            except:
                symbol_font = price_font = ImageFont.load_default()

            draw.text((2, 2), symbol, fill=(255, 255, 255), font=symbol_font)
            draw.text((2, 18), price, fill=(200, 200, 200), font=price_font)
            draw.text((36, 18), change, fill=color, font=price_font)

            frames.append(img)
        
        return frames
    
    def needs_refresh(self) -> bool:
        # Refresh every 5 minutes
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
