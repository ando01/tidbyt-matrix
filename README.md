# Tidbyt Clone for Raspberry Pi - 32x16 Matrix LED

A complete Tidbyt-inspired display system for Raspberry Pi with a 32x16 RGB LED matrix. Customize apps, control brightness, and cycle through multiple information displays automatically.

## Features

✨ **App System**
- Clock with live time display
- Weather information (extensible)
- Stock ticker (mock data ready for API integration)
- Animated art/patterns
- News headlines with scrolling text
- Easy to add custom apps

🎛️ **Control Options**
- Web-based dashboard (http://localhost:5000)
- Command-line interface
- JSON configuration file
- Dynamic brightness control
- Enable/disable apps on the fly

📱 **Display Features**
- Automatic app rotation
- Per-app display duration
- Smooth frame animations
- Real-time clock display
- Colored text and graphics

## Hardware Requirements

- Raspberry Pi (tested on Pi 4, works on Pi 3B+)
- 32x16 RGB LED Matrix Panel
- Appropriate HAT/adapter:
  - **Adafruit RGB Matrix + Real Time Clock HAT** (recommended)
  - Alternative: GPIO ribbon cable with level shifter

### Wiring Guide

If using Adafruit HAT:
```
Plug HAT directly onto 40-pin GPIO header
Connect matrix power supply to HAT
```

If using GPIO wiring:
```
Matrix Data (R1) → GPIO 17
Matrix Data (G1) → GPIO 18
Matrix Data (B1) → GPIO 27
Matrix Data (R2) → GPIO 4
Matrix Data (G2) → GPIO 22
Matrix Data (B2) → GPIO 24
Matrix Address (A) → GPIO 23
Matrix Address (B) → GPIO 25
Matrix Address (C) → GPIO 15
Matrix Address (D) → GPIO 26
Matrix Clock → GPIO 11
Matrix Strobe → GPIO 12
Matrix OE → GPIO 13
```

**Level Shifter Required!** GPIO outputs are 3.3V, matrix expects 5V.

## Installation

### 1. Update Raspberry Pi

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Install build tools
sudo apt install -y git build-essential python3-dev python3-pip

# Install graphics libraries
sudo apt install -y libpython3-dev libtool automake pkg-config

# Install Flask for web UI
pip install --break-system-packages flask pillow
```

### 3. Install RGB Matrix Library

```bash
# Clone the rpi-rgb-led-matrix repository
cd /home/pi
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix

# Build the C++ library
make

# Install Python bindings
cd python
pip install --break-system-packages -e .
```

### 4. Copy Tidbyt Files

```bash
# Create directory for Tidbyt
mkdir -p ~/tidbyt
cd ~/tidbyt

# Copy all the Python files:
# - tidbyt_matrix.py
# - tidbyt_apps.py
# - tidbyt_main.py
# - tidbyt_web.py
```

### 5. Run the Display

#### Option A: Web Dashboard (Recommended)

```bash
cd ~/tidbyt
python3 tidbyt_web.py
```

Then open your browser to: **http://raspberrypi.local:5000**

#### Option B: Command Line Interface

```bash
cd ~/tidbyt
python3 tidbyt_main.py
```

Commands:
```
list                    - List all apps
enable <app>            - Enable an app (e.g., 'enable clock')
disable <app>           - Disable an app
brightness <0-100>      - Set brightness level
save                    - Save configuration to file
help                    - Show help
exit                    - Exit program
```

#### Option C: Direct Python

```bash
python3 -c "from tidbyt_main import TidbytDisplay; d = TidbytDisplay(); d.start(); import time; time.sleep(120)"
```

## Configuration

Configuration is stored in `tidbyt_config.json`:

```json
{
  "brightness": 100,
  "apps": {
    "clock": {"enabled": true, "priority": 10},
    "weather": {"enabled": true, "priority": 5},
    "stocks": {"enabled": true, "priority": 5},
    "art": {"enabled": true, "priority": 1},
    "news": {"enabled": false, "priority": 3}
  }
}
```

**Priority**: Higher numbers show first when cycling through apps
**Display Duration**: How long each app shows (10 seconds by default)

## Creating Custom Apps

Create a new file `custom_app.py`:

```python
from tidbyt_apps import MatrixApp, AppConfig
from PIL import Image, ImageDraw, ImageFont
import time

class MyCustomApp(MatrixApp):
    def __init__(self, config=None):
        super().__init__("Custom", config)
    
    def get_frames(self):
        """Return list of PIL Images"""
        frames = []
        
        # Create frames
        for i in range(30):
            img = Image.new('RGB', (32, 16), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Your drawing code here
            draw.text((5, 5), f"Frame {i}", fill=(255, 255, 255))
            
            frames.append(img)
        
        return frames
    
    def needs_refresh(self):
        """Check if data needs updating"""
        return time.time() - self.last_refresh > 300
```

Then add to `tidbyt_main.py`:

```python
from custom_app import MyCustomApp

# In _setup_apps():
if apps_config.get('custom', {}).get('enabled', True):
    custom_cfg = AppConfig(
        enabled=True,
        priority=5,
        display_duration=10
    )
    self.app_manager.add_app(MyCustomApp(custom_cfg))
```

## API Integration Examples

### Adding Real Weather Data

```python
import requests

class WeatherAppReal(MatrixApp):
    def __init__(self, config=None):
        super().__init__("Weather", config)
        self.api_key = config.config.get('api_key', '') if config else ''
        self.location = config.config.get('location', 'Boston') if config else 'Boston'
    
    def get_frames(self):
        try:
            # Open-Meteo is free, no API key needed
            url = f"https://api.open-meteo.com/v1/forecast?latitude=42.36&longitude=-71.06&current=temperature_2m,weather_code"
            r = requests.get(url, timeout=5)
            data = r.json()
            temp = int(data['current']['temperature_2m'])
            
            img = Image.new('RGB', (32, 16), (0, 0, 10))
            draw = ImageDraw.Draw(img)
            draw.text((4, 5), f"{temp}°F", fill=(100, 200, 255))
            
            return [img] * 30
        except:
            return self._error_frame()
```

### Adding Real Stock Data

```python
class StockAppReal(MatrixApp):
    def get_frames(self):
        try:
            # Using yfinance (install: pip install yfinance)
            import yfinance as yf
            
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            price = info['currentPrice']
            change = info['currentPrice'] - info['previousClose']
            
            frames = []
            # Create display frames with price...
            
            return frames
        except:
            return self._error_frame()
```

### Red Sox Scores (Your Interest!)

```python
class RedSoxApp(MatrixApp):
    def get_frames(self):
        try:
            # Using MLB Stats API (free, no auth)
            import requests
            
            # Get Red Sox game info
            url = "https://statsapi.mlb.com/api/v1/teams/111"
            team_data = requests.get(url).json()
            
            # Get current score
            url = "https://statsapi.mlb.com/api/v1/teams/111/schedule?season=2024"
            games = requests.get(url).json()['records']
            
            # Find today's game and display score...
            
            return frames
        except:
            return self._error_frame()
```

## Troubleshooting

### Display shows nothing

1. Check matrix power supply is connected
2. Verify GPIO pins are correct for your setup
3. Run test: `python3 tidbyt_matrix.py`
4. Check for permission errors: `sudo python3 tidbyt_web.py`

### Slow/choppy animation

1. Reduce frame count in apps
2. Lower brightness slightly
3. Ensure adequate power supply (5V, 4A+ for full brightness)
4. Update rpi-rgb-led-matrix library

### Permission denied errors

The rpi-rgb-led-matrix library requires root access to GPIO:

```bash
sudo python3 tidbyt_web.py
```

Or run as service:

```bash
sudo nano /etc/systemd/system/tidbyt.service
```

```ini
[Unit]
Description=Tidbyt Display Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tidbyt
ExecStart=/usr/bin/python3 /home/pi/tidbyt/tidbyt_web.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable tidbyt
sudo systemctl start tidbyt
```

## Next Steps

1. **Add more apps**: Create weather, stocks, transit using public APIs
2. **Add sports scores**: MLB, NFL, NBA APIs for live scores
3. **Integrate home automation**: Show Home Assistant data
4. **Add notifications**: Display alerts and messages
5. **Photo slideshow**: Display images from folder
6. **Network integration**: Pull data from other devices on your network

## Performance Tips

- **Use appropriate refresh intervals**: Clock every 10s, Weather every 10m, Stocks every 5m
- **Cache API responses**: Don't fetch every frame
- **Limit frame count**: 30 frames is usually enough
- **Disable animations**: Simpler layouts work better on small displays
- **Use fewer colors**: Stick to primary RGB values for clarity

## Project Structure

```
tidbyt/
├── tidbyt_matrix.py      # Low-level matrix control
├── tidbyt_apps.py        # App framework and examples
├── tidbyt_main.py        # CLI and app management
├── tidbyt_web.py         # Web dashboard
├── tidbyt_config.json    # Configuration (auto-generated)
└── README.md            # This file
```

## Resources

- **rpi-rgb-led-matrix**: https://github.com/hzeller/rpi-rgb-led-matrix
- **Adafruit RGB Matrix HAT**: https://www.adafruit.com/product/2345
- **Tidbyt SDK**: https://tidbyt.dev
- **PIL/Pillow Docs**: https://pillow.readthedocs.io
- **Open-Meteo Weather API**: https://open-meteo.com (free!)
- **MLB Stats API**: https://statsapi.mlb.com (free!)

## License

Free to use and modify. Enjoy your retro pixel display!

---

**Happy displaying!** 🎨✨
