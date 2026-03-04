# Tidbyt for Raspberry Pi - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install on Raspberry Pi

```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y git build-essential python3-dev python3-pip libpython3-dev
pip install --break-system-packages flask pillow

# Install RGB matrix library
cd /home/pi
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make
cd python && pip install --break-system-packages -e .

# Create tidbyt directory
mkdir -p ~/tidbyt && cd ~/tidbyt

# Copy your downloaded files here
# (scp them from your computer or clone from GitHub)
```

### 2. Start the Display

**Option A: Web Dashboard** (easiest)
```bash
sudo python3 tidbyt_web.py
```
Then go to: `http://raspberrypi.local:5000`

**Option B: Command Line**
```bash
sudo python3 tidbyt_main.py
```

### 3. Configure

Edit `tidbyt_config.json` to enable/disable apps and adjust brightness.

## 🎯 What You Get

- ✅ **Clock**: Real-time display with flashing colons
- ✅ **Weather**: Mock data (ready to integrate with API)
- ✅ **Stocks**: Mock ticker (ready for yfinance)
- ✅ **Art**: Animated patterns
- ✅ **News**: Scrolling headlines
- ✅ **Web Dashboard**: Easy control from any browser
- ✅ **CLI**: Command-line control

## 🎨 Adding Red Sox Scores

Since you're a Red Sox fan! Add this to a new file `red_sox_app.py`:

```python
from tidbyt_apps import MatrixApp, AppConfig
from PIL import Image, ImageDraw, ImageFont
import requests
import time

class RedSoxApp(MatrixApp):
    def __init__(self, config=None):
        super().__init__("RedSox", config)
    
    def get_frames(self):
        try:
            # Get Red Sox team ID
            url = "https://statsapi.mlb.com/api/v1/teams/111/schedule?season=2024"
            games = requests.get(url, timeout=5).json()
            
            if games['records']:
                game = games['records'][0]  # Latest game
                
                home_team = game['teams']['home']['team']['name']
                away_team = game['teams']['away']['team']['name']
                home_score = game['teams']['home']['score']
                away_score = game['teams']['away']['score']
                status = game['status']['detailedState']
                
                frames = []
                
                # Frame 1: Teams
                img = Image.new('RGB', (32, 16), (0, 0, 20))
                draw = ImageDraw.Draw(img)
                font = ImageFont.load_default()
                draw.text((2, 2), "RED SOX", fill=(255, 100, 100))
                draw.text((2, 9), home_team[:10], fill=(200, 200, 200))
                frames.append(img)
                
                # Frame 2: Score
                img = Image.new('RGB', (32, 16), (0, 0, 20))
                draw = ImageDraw.Draw(img)
                draw.text((4, 5), f"{away_score} - {home_score}", fill=(255, 255, 100))
                frames.append(img)
                
                # Frame 3: Status
                img = Image.new('RGB', (32, 16), (0, 0, 20))
                draw = ImageDraw.Draw(img)
                draw.text((2, 6), status[:16], fill=(150, 200, 255))
                frames.append(img)
                
                return frames * 10  # Repeat frames
        except Exception as e:
            print(f"Red Sox error: {e}")
        
        return self._error_frame()
    
    def _error_frame(self):
        img = Image.new('RGB', (32, 16), (20, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 6), "No data", fill=(255, 100, 100))
        return [img] * 30
    
    def needs_refresh(self):
        return time.time() - self.last_refresh > 600  # 10 minutes
```

Then add to `tidbyt_main.py` in the `_setup_apps()` method:

```python
from red_sox_app import RedSoxApp

# Add with other apps:
if apps_config.get('redsox', {}).get('enabled', True):
    sox_cfg = AppConfig(
        enabled=True,
        priority=8,  # High priority
        display_duration=15
    )
    self.app_manager.add_app(RedSoxApp(sox_cfg))
```

## 🔌 Hardware Setup

**If using Adafruit HAT:**
```
Just plug it straight into GPIO header
No soldering needed!
```

**If using loose wiring:**
Refer to the full README.md for GPIO pin mapping and level shifter requirements.

## 💡 Pro Tips

1. **Matrix power supply**: Get a good 5V 4A+ supply
2. **Run as service**: Use systemd to start at boot
3. **Update rpi-rgb-led-matrix**: Regularly pull latest from GitHub
4. **Test fonts**: Different font sizes work better for different content
5. **Cache API responses**: Don't hammer APIs every frame

## 🐛 Common Issues

**"Permission denied"**
```bash
sudo python3 tidbyt_web.py  # Use sudo
```

**"No module named rgbmatrix"**
```bash
cd ~/rpi-rgb-led-matrix/python
sudo pip install --break-system-packages -e .
```

**Display is dark/dim**
- Check power supply
- Adjust brightness in web UI or config
- Test with `sudo python3 tidbyt_matrix.py`

**Slow animations**
- Reduce frame count in apps
- Check CPU usage: `top`
- Update library: `cd ~/rpi-rgb-led-matrix && git pull && make`

## 📚 Next Steps

1. **Add real weather**: Use Open-Meteo (free, no API key!)
2. **Add stocks**: Use yfinance library
3. **Add transit**: Integrate with your local transit API
4. **Photo display**: Show images from a folder
5. **Smart home**: Pull data from Home Assistant
6. **Custom art**: Create unique pixel animations

## 🚀 Resources

- Full README with detailed setup
- rpi-rgb-led-matrix: https://github.com/hzeller/rpi-rgb-led-matrix
- MLB Stats API: https://statsapi.mlb.com
- Open-Meteo Weather: https://open-meteo.com
- Tidbyt Dev: https://tidbyt.dev

---

**Questions? Check the full README.md for comprehensive documentation!**
