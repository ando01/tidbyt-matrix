# Pushing Tidbyt Project to GitHub

Complete guide to create a GitHub repository and push all files.

## Prerequisites

- GitHub account (create at https://github.com if needed)
- Git installed on your computer

```bash
# Check if git is installed
git --version

# If not installed:
# macOS: brew install git
# Ubuntu/Debian: sudo apt install git
# Windows: Download from https://git-scm.com
```

## Step 1: Create GitHub Repository

### Option A: Using Web Browser (Easiest)

1. Go to https://github.com/new
2. Fill in:
   - **Repository name**: `tidbyt-matrix`
   - **Description**: `Tidbyt-like display system for Raspberry Pi with 32x16 RGB LED matrix`
   - **Visibility**: Public (or Private if you prefer)
   - **Initialize repository**: Check "Add a README file"
3. Click **Create repository**

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if needed
# macOS: brew install gh
# Ubuntu: sudo apt install gh

# Login to GitHub
gh auth login

# Create repository
gh repo create tidbyt-matrix \
  --description "Tidbyt-like display system for Raspberry Pi with 32x16 RGB LED matrix" \
  --public \
  --source=/path/to/tidbyt-files
```

## Step 2: Prepare Your Local Repository

```bash
# Create a folder for your project (if not already created)
mkdir ~/tidbyt-matrix
cd ~/tidbyt-matrix

# Initialize git repository
git init

# Configure git with your GitHub credentials
git config user.name "Your Name"
git config user.email "your-email@example.com"

# Or set globally (recommended)
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

## Step 3: Add All Files

From the outputs folder, copy these files to your local repository:

```bash
cd ~/tidbyt-matrix

# Core Python files
cp /path/to/outputs/tidbyt_matrix.py .
cp /path/to/outputs/tidbyt_apps.py .
cp /path/to/outputs/tidbyt_main.py .
cp /path/to/outputs/tidbyt_web.py .
cp /path/to/outputs/real_api_examples.py .

# Documentation files
cp /path/to/outputs/README.md .
cp /path/to/outputs/QUICKSTART.md .
cp /path/to/outputs/EMULATOR_README.md .
cp /path/to/outputs/EMULATOR_GUIDE.md .
cp /path/to/outputs/EMULATOR_QUICK_REFERENCE.md .
cp /path/to/outputs/EMULATOR_INTEGRATION.md .
cp /path/to/outputs/EMULATOR_FEATURES.txt .
cp /path/to/outputs/EMULATOR_INDEX.md .
cp /path/to/outputs/SYSTEMD_SETUP.md .

# Service files
cp /path/to/outputs/tidbyt.service .
cp /path/to/outputs/tidbyt-web.service .

# Features list
cp /path/to/outputs/EMULATOR_FEATURES.txt .
```

## Step 4: Create .gitignore File

```bash
cd ~/tidbyt-matrix

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Config files (with secrets)
tidbyt_config.json
*.env

# Temporary files
*.log
.cache/
tmp/

# OS
.DS_Store
Thumbs.db
EOF

git add .gitignore
```

## Step 5: Create README.md (Main)

If you don't have one, create a comprehensive README:

```bash
cat > README.md << 'EOF'
# Tidbyt Matrix Display

A complete Tidbyt-inspired display system for Raspberry Pi with 32×16 RGB LED matrix.

## Features

✨ **Display System**
- App framework with modular design
- Clock, Weather, Stocks, Art, News apps
- Extensible for custom apps
- Real-time updates

🎨 **Web Dashboard**
- Live 32×16 pixel matrix emulator
- Brightness control
- App management
- Remote access via browser

🎮 **Control Options**
- Web UI dashboard
- Command-line interface
- Configuration file (JSON)
- Systemd service

## Hardware

- Raspberry Pi (3B+, 4, or Zero 2W)
- 32×16 RGB LED Matrix Panel
- Appropriate HAT or GPIO wiring

## Quick Start

### Install

```bash
cd /home/andy/tidbyt
sudo apt update && sudo apt upgrade -y
sudo apt install -y git build-essential python3-dev python3-pip libpython3-dev
pip install --break-system-packages flask pillow

# Install RGB matrix library
cd /home/andy
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make
cd python
pip install --break-system-packages -e .
```

### Run

```bash
cd /home/andy/tidbyt

# Web Dashboard
sudo python3 tidbyt_web.py
# Open: http://raspberrypi.local:5000

# Or CLI
sudo python3 tidbyt_main.py
```

## Documentation

- **README.md** - This file
- **QUICKSTART.md** - 5-minute setup guide
- **EMULATOR_README.md** - Web emulator overview
- **EMULATOR_GUIDE.md** - Detailed emulator features
- **EMULATOR_INTEGRATION.md** - Advanced customization
- **SYSTEMD_SETUP.md** - Run as system service

## File Structure

```
tidbyt-matrix/
├── tidbyt_matrix.py          # Low-level matrix control
├── tidbyt_apps.py            # App framework & examples
├── tidbyt_main.py            # CLI controller
├── tidbyt_web.py             # Web dashboard
├── real_api_examples.py      # Real API integrations
├── tidbyt.service            # Systemd service file
├── tidbyt-web.service        # Systemd web service
├── README.md                 # This file
├── QUICKSTART.md             # Quick start guide
└── docs/
    ├── EMULATOR_*.md         # Emulator documentation
    ├── SYSTEMD_SETUP.md      # Service setup
    └── EMULATOR_FEATURES.txt # Feature summary
```

## Creating Apps

See `real_api_examples.py` for examples:

```python
from tidbyt_apps import MatrixApp, AppConfig
from PIL import Image, ImageDraw
import time

class MyApp(MatrixApp):
    def __init__(self, config=None):
        super().__init__("MyApp", config)
    
    def get_frames(self):
        frames = []
        # Create your frames here
        return frames
    
    def needs_refresh(self):
        return time.time() - self.last_refresh > 300
```

## API Examples

### Weather (Open-Meteo - Free)
```python
from real_api_examples import WeatherAppReal

weather = WeatherAppReal()
weather.fetch_weather()
frames = weather.get_frames()
```

### Stocks (yfinance)
```python
from real_api_examples import StockAppReal

stocks = StockAppReal(config)
stocks.fetch_stocks()
frames = stocks.get_frames()
```

### Red Sox Scores (MLB Stats API)
```python
from real_api_examples import RedSoxApp

sox = RedSoxApp()
sox.fetch_game()
frames = sox.get_frames()
```

## Configuration

Edit `tidbyt_config.json`:

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

## Performance

- **CPU Usage**: <5% on Pi 4, <10% on Pi Zero 2W
- **Network**: ~20KB per 100ms for web dashboard
- **Update Rate**: 10 FPS default (adjustable)
- **Memory**: ~50-100MB for web server

## Browser Support

✅ Chrome, Firefox, Safari, Edge
⚠️ Mobile browsers (fully responsive)
❌ Internet Explorer

## System Service

Run as background service:

```bash
sudo cp tidbyt-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tidbyt-web.service
sudo systemctl start tidbyt-web.service
```

See `SYSTEMD_SETUP.md` for details.

## Troubleshooting

### Display shows nothing
- Check matrix power supply
- Verify GPIO pins
- Run: `sudo python3 tidbyt_matrix.py` to test

### Permission denied
- Use `sudo` for GPIO access
- Or add user to gpio group: `sudo usermod -a -G gpio andy`

### Web dashboard slow on Pi Zero 2W
- Reduce update frequency in `tidbyt_web.py`
- Change `setInterval(updateDisplay, 100)` to `setInterval(updateDisplay, 200)`

## Future Features

- [ ] WebSocket real-time sync
- [ ] Multi-display control
- [ ] Screenshot export
- [ ] Video recording
- [ ] Performance dashboard
- [ ] Mobile app

## Contributing

Contributions welcome! Feel free to:
- Add new apps
- Improve documentation
- Optimize performance
- Add tests

## License

MIT License - Free to use and modify

## Resources

- **rpi-rgb-led-matrix**: https://github.com/hzeller/rpi-rgb-led-matrix
- **Tidbyt SDK**: https://tidbyt.dev
- **Open-Meteo Weather API**: https://open-meteo.com
- **MLB Stats API**: https://statsapi.mlb.com

## Author

Created for Raspberry Pi with 32×16 RGB LED matrix displays.

---

**Happy displaying!** 🎨✨
EOF

git add README.md
```

## Step 6: Add Files to Git

```bash
cd ~/tidbyt-matrix

# Add all files
git add .

# Check what will be committed
git status

# Commit with message
git commit -m "Initial commit: Tidbyt display system for Raspberry Pi

- Core display control library (tidbyt_matrix.py)
- App framework with examples (tidbyt_apps.py)
- CLI controller (tidbyt_main.py)
- Web dashboard with live emulator (tidbyt_web.py)
- Real API integration examples
- Comprehensive documentation
- Systemd service files"
```

## Step 7: Connect to GitHub and Push

```bash
# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tidbyt-matrix.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 8: Verify on GitHub

1. Go to https://github.com/YOUR_USERNAME/tidbyt-matrix
2. You should see all your files
3. README should display nicely

## Alternative: Using Personal Access Token

If you get authentication errors:

```bash
# Generate PAT on GitHub:
# Settings → Developer settings → Personal access tokens → Generate new token
# Scopes: repo, workflow

# Use PAT for authentication
git remote set-url origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/tidbyt-matrix.git

git push -u origin main
```

## Making Updates

After initial push, to update your repo:

```bash
cd ~/tidbyt-matrix

# Make changes to files
# ... edit files ...

# Stage changes
git add .

# Commit
git commit -m "Brief description of changes"

# Push to GitHub
git push origin main
```

## Useful Git Commands

```bash
# Check status
git status

# View commit history
git log --oneline

# View changes before committing
git diff

# View remote details
git remote -v

# Pull latest changes from GitHub
git pull origin main

# Create a new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Delete local branch
git branch -d branch-name
```

## Setting Up on New Pi

Once on GitHub, clone to your Pi:

```bash
cd /home/andy
git clone https://github.com/YOUR_USERNAME/tidbyt-matrix.git
cd tidbyt-matrix

# Install dependencies
pip install --break-system-packages flask pillow
# ... etc

# Run
sudo python3 tidbyt_web.py
```

## Share Your Repo

- Add to GitHub profile
- Share the link: `https://github.com/YOUR_USERNAME/tidbyt-matrix`
- Collaborate with others
- Get feedback from community

## Tips

1. **License**: Add LICENSE file for open source
   ```bash
   # MIT license is recommended
   # https://choosealicense.com/
   ```

2. **Tags**: Mark releases
   ```bash
   git tag -a v1.0.0 -m "First release"
   git push origin v1.0.0
   ```

3. **.gitignore**: Already covered, protects secrets

4. **Collaborators**: Invite others to contribute
   - GitHub → Settings → Collaborators

5. **Documentation**: Keep README and docs updated

---

**Questions?** Check GitHub docs: https://docs.github.com
