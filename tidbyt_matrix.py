#!/usr/bin/env python3
"""
Matrix LED Display Controller for Raspberry Pi
Supports 32x16 RGB matrices connected via GPIO
"""

import time
import threading
from dataclasses import dataclass
from typing import Optional, Callable
from PIL import Image, ImageDraw, ImageFont
import os

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:
    print("Installing rpi-rgb-led-matrix...")
    os.system("pip install --break-system-packages rpi-rgb-led-matrix pillow")
    from rgbmatrix import RGBMatrix, RGBMatrixOptions


@dataclass
class MatrixConfig:
    """Configuration for RGB LED matrix"""
    rows: int = 16
    cols: int = 32
    brightness: int = 100
    gpio_slowdown: int = 4
    
    def to_options(self) -> RGBMatrixOptions:
        """Convert config to RGBMatrixOptions"""
        options = RGBMatrixOptions()
        options.rows = self.rows
        options.cols = self.cols
        options.brightness = self.brightness
        options.gpio_slowdown = self.gpio_slowdown
        options.hardware_mapping = 'adafruit-hat'
        options.row_address_type = 1
        options.pwm_bits = 11
        options.pwm_lsb_nanoseconds = 130
        options.led_rgb_sequence = "RGB"
        options.pixel_mapper_config = ""
        options.panel_type = ""
        options.multiplexing = 0
        options.disable_hardware_pulsing = True
        options.show_refresh_rate = False
        options.limit_refresh_rate_hz = 0
        return options


class MatrixDisplay:
    """Control the LED matrix display"""
    
    def __init__(self, config: Optional[MatrixConfig] = None):
        """Initialize matrix display"""
        self.config = config or MatrixConfig()
        self.matrix = RGBMatrix(options=self.config.to_options())
        self.current_image = Image.new('RGB', (self.config.cols, self.config.rows))
        self.lock = threading.Lock()
        self.is_running = False
        
    def draw_image(self, image: Image.Image):
        """Draw PIL image to matrix"""
        with self.lock:
            # Ensure image is correct size and format
            if image.size != (self.config.cols, self.config.rows):
                image = image.resize((self.config.cols, self.config.rows), Image.Resampling.LANCZOS)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            self.current_image = image
            self.matrix.SetImage(image)
    
    def draw_text(self, text: str, x: int = 0, y: int = 0, 
                  color: tuple = (255, 255, 255), 
                  font_size: int = 6,
                  background: tuple = (0, 0, 0)):
        """Draw text on matrix"""
        image = Image.new('RGB', (self.config.cols, self.config.rows), background)
        draw = ImageDraw.Draw(image)
        
        # Try to load a small font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text((x, y), text, fill=color, font=font)
        self.draw_image(image)
    
    def clear(self):
        """Clear the display"""
        self.draw_image(Image.new('RGB', (self.config.cols, self.config.rows), (0, 0, 0)))
    
    def set_brightness(self, brightness: int):
        """Set brightness (0-100)"""
        self.config.brightness = max(0, min(100, brightness))
        self.matrix.brightness = self.config.brightness
    
    def get_brightness(self) -> int:
        """Get current brightness"""
        return self.config.brightness
    
    def close(self):
        """Clean up resources"""
        self.matrix.Clear()
        del self.matrix
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class ScrollingText:
    """Helper for scrolling text animation"""
    
    def __init__(self, text: str, color: tuple = (255, 255, 255),
                 bg_color: tuple = (0, 0, 0), font_size: int = 6,
                 speed: float = 0.05):
        self.text = text
        self.color = color
        self.bg_color = bg_color
        self.font_size = font_size
        self.speed = speed
        
    def generate_frames(self, width: int, height: int, frames: int = None) -> list:
        """Generate scrolling text frames"""
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", self.font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text dimensions
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        bbox = temp_draw.textbbox((0, 0), self.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Generate frames for scrolling
        frames_list = []
        total_distance = width + text_width
        num_frames = frames or int(total_distance / (self.speed * 60))
        
        for frame in range(num_frames):
            x_pos = width - int(frame * self.speed * 60)
            
            img = Image.new('RGB', (width, height), self.bg_color)
            draw = ImageDraw.Draw(img)
            y_pos = max(0, (height - text_height) // 2)
            draw.text((x_pos, y_pos), self.text, fill=self.color, font=font)
            
            frames_list.append(img)
        
        return frames_list


if __name__ == "__main__":
    # Test the display
    with MatrixDisplay() as display:
        # Test 1: Draw some text
        display.draw_text("HELLO WORLD!", x=0, y=5, color=(255, 0, 0))
        time.sleep(2)
        
        # Test 2: Clear and test different color
        display.draw_text("32x16", x=6, y=5, color=(0, 255, 0))
        time.sleep(2)
        
        display.clear()
