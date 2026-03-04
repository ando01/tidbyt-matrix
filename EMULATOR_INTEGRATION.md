# Integrating the Matrix Display Emulator

This guide shows how to add the emulator to your existing Tidbyt setup, customize it, and integrate it into other projects.

## Installation

### Quick Replacement
If you already have `tidbyt_web.py`, simply replace it:

```bash
cd ~/tidbyt
cp tidbyt_web.py tidbyt_web.py.backup
# Copy the new tidbyt_web.py from outputs
sudo python3 tidbyt_web.py
```

### From Scratch
```bash
mkdir -p ~/tidbyt
cd ~/tidbyt
# Copy all files including the updated tidbyt_web.py
sudo python3 tidbyt_web.py
```

### Start the Service
```bash
sudo systemctl restart tidbyt-web.service
# or
sudo python3 tidbyt_web.py
```

## What Changed

### New API Endpoint
```
GET /api/display
Returns: {
  "frame_data": "base64 PNG",
  "current_app": "Clock",
  "width": 32,
  "height": 16
}
```

### New JavaScript Features
- Matrix grid initialization
- Pixel rendering from image data
- Real-time updates (100ms default)
- Canvas-based image processing

### New CSS Styles
- Matrix display grid layout
- Pixel styling with glow effects
- Responsive container design
- Dark theme for better visibility

## Customization

### 1. Change Update Frequency

Edit the interval in JavaScript section:

```javascript
// Find this line (around line 380)
setInterval(updateDisplay, 100);

// Change to your desired interval (milliseconds)
setInterval(updateDisplay, 50);   // 20 FPS - very smooth
setInterval(updateDisplay, 200);  // 5 FPS - light on resources
```

### 2. Adjust Pixel Size

Modify CSS for different pixel dimensions:

```css
#matrix-display {
    width: 400px;   /* Smaller display */
    height: 200px;
    grid-template-columns: repeat(32, 1fr);
}

.pixel {
    width: 12px;    /* Smaller pixels */
    height: 12px;
}
```

Pixel size chart:
- **12px**: Compact (320×160 total)
- **16px**: Default (520×260 total)
- **20px**: Large (656×320 total)
- **24px**: Very Large (800×384 total)

### 3. Change Pixel Appearance

Customize the look and feel:

```css
.pixel {
    /* Off pixel styling */
    background: #050505;           /* Even darker */
    border-radius: 1px;            /* Less rounded */
    box-shadow: none;              /* No inset shadow */
}

.pixel.active {
    /* Lit pixel styling */
    box-shadow: 0 0 10px currentColor,  /* Bigger glow */
                inset 0 1px 1px rgba(255,255,255,0.5);
}
```

### 4. Change Update Behavior

Modify how the display refreshes:

```javascript
// Slow updates if network is slow
async function updateDisplayWithFallback() {
    try {
        await updateDisplay();
    } catch (error) {
        console.warn('Display update failed, retrying...');
        setTimeout(updateDisplayWithFallback, 500);
    }
}

setInterval(updateDisplayWithFallback, 100);
```

### 5. Add Performance Monitoring

Track update performance:

```javascript
let frameCount = 0;
let lastFpsTime = Date.now();

async function updateDisplayWithStats() {
    const startTime = Date.now();
    await updateDisplay();
    const duration = Date.now() - startTime;
    
    frameCount++;
    const elapsed = Date.now() - lastFpsTime;
    if (elapsed >= 1000) {
        console.log(`FPS: ${frameCount}, Frame time: ${duration}ms`);
        frameCount = 0;
        lastFpsTime = Date.now();
    }
}
```

## Integration Examples

### Example 1: Standalone Emulator Page

Create a minimal emulator-only page:

```python
from flask import Flask, render_template_string

app = Flask(__name__)

EMULATOR_ONLY = """
<!DOCTYPE html>
<html>
<head>
    <title>Tidbyt Emulator</title>
    <style>
        body { background: #000; display: flex; justify-content: center; }
        #matrix-display { 
            display: grid;
            grid-template-columns: repeat(32, 1fr);
            gap: 2px;
            width: 520px;
            height: 260px;
            padding: 10px;
        }
        .pixel { 
            background: #0a0a0a;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div id="matrix-display"></div>
    <script>
        // Matrix initialization and update code here
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(EMULATOR_ONLY)
```

### Example 2: Embed in Dashboard

Add emulator to an existing dashboard:

```html
<!-- In your existing HTML -->
<div class="dashboard-widget">
    <h2>Tidbyt Display</h2>
    <div id="matrix-display"></div>
    <p id="current-app">Loading...</p>
</div>

<script>
// Include the initialization and update functions
// from tidbyt_web.py
</script>
```

### Example 3: WebSocket Real-Time Updates

Replace HTTP polling with WebSocket:

```python
from flask_socketio import SocketIO, emit
import socketio

sio = SocketIO(app, cors_allowed_origins="*")

@sio.on('connect')
def on_connect():
    print('Client connected')
    emit_display_frame()

def emit_display_frame():
    # Get frame data
    frame_data = get_display_frame_base64()
    app_name = tidbyt_display.app_manager.get_current_app().name
    
    # Emit to all connected clients
    sio.emit('display_update', {
        'frame_data': frame_data,
        'current_app': app_name
    }, broadcast=True)
```

JavaScript client:
```javascript
const socket = io();

socket.on('display_update', (data) => {
    updateDisplayFromData(data);
});
```

### Example 4: Multi-Display Control

Control multiple Pi displays from one dashboard:

```python
@app.route('/api/displays', methods=['GET'])
def get_all_displays():
    displays = {
        'living_room': tidbyt_display_1.get_frame(),
        'bedroom': tidbyt_display_2.get_frame(),
        'kitchen': tidbyt_display_3.get_frame(),
    }
    return jsonify(displays)
```

HTML:
```html
<div class="display-grid">
    <div class="display-item">
        <h3>Living Room</h3>
        <div id="matrix-1"></div>
    </div>
    <div class="display-item">
        <h3>Bedroom</h3>
        <div id="matrix-2"></div>
    </div>
    <div class="display-item">
        <h3>Kitchen</h3>
        <div id="matrix-3"></div>
    </div>
</div>
```

### Example 5: Mobile App Integration

Use the emulator API in a mobile app:

```javascript
// React Native / Flutter web view
async function fetchDisplayFrame() {
    const response = await fetch('http://pi.local:5000/api/display');
    const data = await response.json();
    
    // Display frame_data as image
    renderImageToScreen(data.frame_data);
    updateAppName(data.current_app);
}
```

## Advanced Customization

### Custom Pixel Rendering

Replace canvas-based rendering with your own:

```javascript
function setPixelCustom(x, y, r, g, b) {
    const pixel = document.getElementById(`pixel-${x}-${y}`);
    
    // Custom logic
    if (r > 200 && g < 50 && b < 50) {
        pixel.style.filter = 'drop-shadow(0 0 5px red)';
    }
    
    pixel.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
}
```

### Add Statistics Display

Show real-time statistics:

```javascript
let stats = {
    updates: 0,
    avgTime: 0,
    fps: 0,
    memoryUsage: 0
};

function updateStats() {
    document.getElementById('stats').innerHTML = `
        <p>Updates: ${stats.updates}</p>
        <p>Avg Frame Time: ${stats.avgTime}ms</p>
        <p>FPS: ${stats.fps}</p>
    `;
}
```

### Theme Support

Add light/dark theme:

```css
:root {
    --bg-color: #000;
    --pixel-off: #0a0a0a;
    --pixel-border: #222;
}

body.light-theme {
    --bg-color: #fff;
    --pixel-off: #ddd;
    --pixel-border: #ccc;
}

#matrix-display {
    background: var(--bg-color);
    border-color: var(--pixel-border);
}

.pixel {
    background: var(--pixel-off);
}
```

## Performance Optimization

### 1. Use RequestAnimationFrame

For smoother updates:

```javascript
function smoothUpdate() {
    updateDisplay();
    requestAnimationFrame(smoothUpdate);
}

smoothUpdate();
```

### 2. Implement Dirty Rectangle Optimization

Only update changed pixels:

```javascript
let lastFrame = null;

function updateDisplayOptimized() {
    const newFrame = getDisplayData();
    
    for (let i = 0; i < 32 * 16; i++) {
        if (newFrame[i] !== lastFrame[i]) {
            updatePixel(i, newFrame[i]);
        }
    }
    
    lastFrame = newFrame;
}
```

### 3. Use Web Workers

Offload processing:

```javascript
// worker.js
self.onmessage = function(e) {
    const imageData = e.data;
    const pixelData = processImage(imageData);
    self.postMessage(pixelData);
};

// main.js
const worker = new Worker('worker.js');
worker.postMessage(imageData);
worker.onmessage = (e) => renderPixels(e.data);
```

## Debugging

### Enable Console Logging

```javascript
// Add to updateDisplay function
console.log('Fetching display...');
console.time('display-update');
// ... update code ...
console.timeEnd('display-update');
```

### Monitor Network

```javascript
// Check API performance
fetch('/api/display')
    .then(r => {
        console.log('Response time:', new Date() - startTime, 'ms');
        return r.json();
    });
```

### Pixel Inspection

Add hover inspection:

```javascript
document.addEventListener('mousemove', function(e) {
    const pixel = e.target;
    if (pixel.classList.contains('pixel')) {
        const color = window.getComputedStyle(pixel).backgroundColor;
        console.log('Pixel color:', color);
    }
});
```

## Deployment

### Production Checklist

- [ ] Set `debug=False` in Flask
- [ ] Use production WSGI server (Gunicorn)
- [ ] Set appropriate CORS headers
- [ ] Enable HTTPS if accessible over internet
- [ ] Configure firewall rules
- [ ] Add authentication if needed
- [ ] Monitor resource usage
- [ ] Set up logging

### Gunicorn Setup

```bash
pip install gunicorn --break-system-packages

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 tidbyt_web:app

# Or in systemd service
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 tidbyt_web:app
```

## Troubleshooting Integration

### Issue: Emulator shows black
**Solution**: Verify app is enabled and display is running

### Issue: Slow updates
**Solution**: 
- Check network latency: `ping raspberrypi.local`
- Reduce update frequency: `setInterval(updateDisplay, 200)`
- Use lighter image format

### Issue: Memory leak
**Solution**: 
- Clear old image data
- Use `requestAnimationFrame` instead of `setInterval`
- Profile in DevTools

### Issue: Out of sync
**Solution**:
- Increase update frequency to 50ms
- Check for dropped frames
- Use WebSocket for real-time sync

## Resources

- Flask Documentation: https://flask.palletsprojects.com/
- Canvas API: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API
- WebSocket: https://socket.io/
- Performance: https://web.dev/performance/

---

Happy integrating! 🚀
