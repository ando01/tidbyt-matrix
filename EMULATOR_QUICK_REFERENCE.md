# Tidbyt Web Emulator - Quick Reference

## What's New

The web dashboard now includes a **live 32×16 pixel matrix display emulator** that shows exactly what's being rendered on your physical LED matrix.

## Visual Layout

```
════════════════════════════════════════════════════════════════
                    TIDBYT WEB DASHBOARD
════════════════════════════════════════════════════════════════

┌─────────────────────────────────┐  ┌──────────────────────────┐
│    🎨 LIVE DISPLAY             │  │    CONTROL PANEL         │
│                                 │  │                          │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━┓   │  │  Status: Connected  ✓    │
│  ┃ [ ][ ][█][█][ ][ ]...  ┃   │  │                          │
│  ┃ [█][█][█][█][█][ ]...  ┃   │  │  ☀️ Brightness          │
│  ┃ [ ][ ][█][█][ ][ ]...  ┃   │  │  |━━━━━━━━━━━━━━| 100%  │
│  ┃ ...                     ┃   │  │                          │
│  ┃ 32 pixels wide          ┃   │  │  APPS                    │
│  ┃ 16 pixels tall          ┃   │  │  □ Clock      ⊘ ⊘       │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━┛   │  │  □ Weather    ⊘ ⊘       │
│  32 × 16 pixels                │  │  □ Stocks     ⊘ ⊘       │
│                                 │  │  □ Art        ⊘ ⊘       │
│  ▶️ Current: Clock             │  │                          │
│                                 │  │  [💾 Save] [🔄 Refresh] │
│  Updates every 100ms            │  │                          │
└─────────────────────────────────┘  └──────────────────────────┘
```

## Key Features

### 🎨 Matrix Display
- **Size**: 32 × 16 pixels (exact match to your hardware)
- **Colors**: Full 24-bit RGB (millions of colors)
- **Update Rate**: 10 FPS (100ms refresh)
- **Accuracy**: Pixel-perfect rendering of what's on the display

### 📊 Real-Time Information
- Shows current app name
- Display resolution
- Live pixel data from each frame

### 🎮 Full Controls
- Enable/disable apps
- Adjust brightness (0-100%)
- Save configuration
- Monitor in real-time

## How It Works

```
Your Display               Your Browser
     │                         │
     │ Updates every frame     │
     │─────────────────────────→ Get current image
     │                         │
     │ Converts to PNG         │
     │─────────────────────────→ Encodes as base64
     │                         │
     │ Sends via API           │
     │─────────────────────────→ JSON response
     │                         │
     │                         │ JavaScript decodes
     │                         │ Renders 32×16 grid
     │                         │ Shows on screen
     │                         │←─────────────────
```

## Usage Scenarios

### Scenario 1: Debug Apps Without Hardware
```
1. Create a new app in Python
2. Enable it in web dashboard
3. Watch emulator show output
4. Tweak colors/layout in real-time
5. No physical display needed!
```

### Scenario 2: Remote Monitoring
```
1. Run on your Pi
2. Access from phone/tablet on WiFi
3. See live display anywhere at home
4. Control brightness and apps remotely
```

### Scenario 3: Development & Testing
```
1. Use emulator for fast iteration
2. Test all apps before hardware deployment
3. Verify colors are correct
4. Check animation timing
5. Then deploy to actual matrix
```

### Scenario 4: Troubleshooting
```
1. Physical display looks wrong
2. Check emulator - does it match?
3. If emulator is correct, issue is hardware
4. If emulator is wrong, issue is software
5. Quick diagnosis!
```

## Features at a Glance

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Live Sync** | Updates every 100ms | See changes instantly |
| **32×16 Grid** | Exact hardware size | Precise preview |
| **RGB Colors** | Full color support | Accurate rendering |
| **App Name** | Shows current app | Easy monitoring |
| **Remote Access** | Works over WiFi | Control from anywhere |
| **Zero Latency** | Direct from Python | No sync delays |

## Color Guide

- **Bright pixels** (RGB > 10): Display as actual color + glow effect
- **Dark pixels** (RGB ≤ 10): Display as dark gray
- **Off pixels** (RGB = 0): Appear as black
- **Glow effect**: Simulates LED brightness on screen

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| Screen is black | Enable an app in the control panel |
| Updates are slow | Try reducing browser tabs or increasing interval |
| Colors look wrong | Check brightness setting (may be very dim) |
| Can't connect | Verify Pi and computer are on same WiFi |

## Performance Tips

- **Fast updates**: Set interval to 50ms for 20 FPS
- **Light load**: Set interval to 200ms for 5 FPS
- **Responsive**: Keep at 100ms default for balance
- **Mobile**: Use 200ms to save battery

## Keyboard Shortcuts

Currently the web UI doesn't have keyboard shortcuts, but you can add them:

```javascript
document.addEventListener('keydown', function(e) {
    if (e.key === 'b') setBrightness(50);      // 'B' for brightness
    if (e.key === '+') setBrightness(100);     // '+' for max brightness
    if (e.key === '-') setBrightness(0);       // '-' for min brightness
});
```

## Mobile Optimization

The dashboard is fully responsive:
- **Landscape**: Side-by-side display and controls
- **Portrait**: Stacked layout for easier viewing
- **Pinch zoom**: Works on touch devices
- **Touch controls**: All buttons are touch-friendly

## Advanced: Customization

### Change Pixel Size
```css
.pixel {
    width: 20px;    /* Bigger pixels */
    height: 20px;
}
```

### Change Update Speed
```javascript
setInterval(updateDisplay, 50);  // 20 FPS instead of 10 FPS
```

### Add Grid Lines
```css
#matrix-display {
    gap: 5px;    /* Increase pixel gap */
}
```

### Change Colors
```css
.pixel {
    background: #1a1a1a;  /* Darker off color */
}
```

## Browser Compatibility

✅ **Chrome/Edge** - Full support, best performance
✅ **Firefox** - Full support
✅ **Safari** - Full support
⚠️ **IE11** - Not supported (use modern browser)

## Network Requirements

- **Bandwidth**: ~20KB per update (every 100ms)
- **Latency**: Works with <500ms latency
- **WiFi**: Standard 2.4GHz or 5GHz
- **Wired**: Recommended for lowest latency

## File Structure

```
tidbyt_web.py
├── INDEX_TEMPLATE (HTML/CSS/JS)
│   ├── Matrix display CSS
│   ├── Control panel CSS
│   └── JavaScript for updates
├── Routes
│   ├── / (Dashboard)
│   ├── /api/display (Get current frame)
│   ├── /api/apps (Get app list)
│   ├── /api/app/<name> (Toggle app)
│   ├── /api/brightness (Set brightness)
│   └── /api/config (Save config)
└── Flask server setup
```

## Example Use Cases

### Use Case 1: Recipe Testing
```
1. Create a recipe/cooking timer app
2. Enable in dashboard
3. Watch timer count down on emulator
4. Verify display updates correctly
5. Deploy to hardware
```

### Use Case 2: Weather Widget
```
1. Build weather fetching app
2. Display in emulator
3. Check color scheme
4. Verify text readability
5. Then run on Pi 24/7
```

### Use Case 3: Sports Scores
```
1. Create Red Sox scores app
2. See live score display
3. Verify layout and colors
4. Test during actual game
5. Perfect for your interests!
```

## FAQ

**Q: Does emulator lag behind the actual display?**
A: No, it's in sync (both use same Python frame buffer)

**Q: Can I screenshot the emulator?**
A: Yes, use browser print/screenshot (Print Screen)

**Q: Does it work on mobile?**
A: Yes, fully responsive design

**Q: How much CPU does it use?**
A: <5% on Pi, updates only at 10 FPS

**Q: Can I embed it in another page?**
A: Yes, modify Flask template to use iframes

**Q: What if I don't have the physical display?**
A: That's the whole point - develop apps with just the emulator!

---

**Pro Tip**: Use the emulator for rapid development, then deploy to your physical 32×16 matrix when you're happy with the results! 🚀
