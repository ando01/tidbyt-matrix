#!/usr/bin/env python3
"""
Web UI for Tidbyt Display Control
Flask-based dashboard for managing apps and display settings
Includes emulated 32x16 matrix display
"""

import json
import time
import threading
from flask import Flask, render_template_string, request, jsonify
from tidbyt_main import TidbytDisplay
from PIL import Image
import os
import base64
from io import BytesIO

app = Flask(__name__)
tidbyt_display = None


# ============================================================================
# WEB TEMPLATES
# ============================================================================

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tidbyt Display Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .main-container {
            display: flex;
            gap: 30px;
            max-width: 1400px;
            width: 100%;
            flex-wrap: wrap;
            justify-content: center;
            align-items: flex-start;
        }
        
        .display-section {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
            text-align: center;
        }
        
        .emulator {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
        }
        
        .emulator h2 {
            color: #333;
            font-size: 1.3em;
            margin-bottom: 10px;
        }
        
        .emulator-frame {
            background: linear-gradient(135deg, #1a1a1a 0%, #000 100%);
            border-radius: 20px;
            padding: 20px;
            box-shadow: inset 0 0 30px rgba(0,0,0,0.8), 0 20px 60px rgba(0,0,0,0.3);
        }
        
        #matrix-display {
            display: grid;
            grid-template-columns: repeat(64, 1fr);
            gap: 2px;
            background: #000;
            padding: 8px;
            border-radius: 8px;
            border: 2px solid #222;
            width: 520px;
            height: 260px;
        }
        
        .pixel {
            width: 100%;
            aspect-ratio: 1;
            border-radius: 2px;
            background: #0a0a0a;
            box-shadow: inset 0 2px 2px rgba(0,0,0,0.9);
            transition: background-color 0.02s linear, box-shadow 0.02s linear;
        }
        
        .pixel.active {
            box-shadow: inset 0 1px 1px rgba(255,255,255,0.2), 0 0 8px rgba(255,255,255,0.3);
        }
        
        .resolution-text {
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
            font-family: monospace;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            color: #667eea;
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .brightness-control {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .brightness-control input {
            flex: 1;
            height: 8px;
            border-radius: 5px;
            border: none;
            background: linear-gradient(to right, #ddd, #667eea);
            outline: none;
            -webkit-appearance: none;
        }
        
        .brightness-control input::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(102, 126, 234, 0.4);
        }
        
        .brightness-control input::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(102, 126, 234, 0.4);
        }
        
        .brightness-value {
            color: #667eea;
            font-weight: 600;
            min-width: 50px;
            text-align: right;
        }
        
        .apps-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .app-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .app-card:hover {
            border-color: #667eea;
            background: #f0f3ff;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }
        
        .app-card.disabled {
            opacity: 0.6;
            background: #e9ecef;
        }
        
        .app-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .app-toggle {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: 0.3s;
            border-radius: 24px;
        }
        
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: 0.3s;
            border-radius: 50%;
        }
        
        input:checked + .toggle-slider {
            background-color: #667eea;
        }
        
        input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        
        .status {
            background: #f0f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #333;
        }
        
        .status-active {
            color: #28a745;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }
        
        button {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #e9ecef;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #dee2e6;
        }
        
        .current-app {
            color: #667eea;
            font-weight: 600;
            margin-top: 10px;
            padding: 10px;
            background: #f0f3ff;
            border-radius: 8px;
        }
        
        @media (max-width: 1200px) {
            .main-container {
                flex-direction: column;
                align-items: center;
            }
            
            #matrix-display {
                width: 400px;
                height: 200px;
            }
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .apps-grid {
                grid-template-columns: 1fr;
            }
            
            #matrix-display {
                width: 320px;
                height: 160px;
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Matrix Display Emulator -->
        <div class="display-section">
            <div class="emulator">
                <h2>🎨 Live Display</h2>
                <div class="emulator-frame">
                    <div id="matrix-display"></div>
                </div>
                <div class="resolution-text">64 × 32 pixels</div>
                <div class="current-app" id="current-app">Loading...</div>
            </div>
        </div>
        
        <!-- Control Panel -->
        <div class="container">
            <h1>Tidbyt Control</h1>
            
            <div class="status">
                <div><strong>Status:</strong> <span class="status-active" id="status">Connected</span></div>
            </div>
            
            <div class="section">
                <div class="section-title">Brightness</div>
                <div class="brightness-control">
                    <span>☀️</span>
                    <input type="range" id="brightness" min="0" max="100" value="100">
                    <div class="brightness-value" id="brightness-value">100%</div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Apps</div>
                <div class="apps-grid" id="apps-grid">
                    <!-- Apps will be loaded here -->
                </div>
            </div>
            
            <div class="button-group">
                <button class="btn-primary" onclick="saveConfig()">💾 Save Config</button>
                <button class="btn-secondary" onclick="reloadApps()">🔄 Refresh</button>
                <button class="btn-secondary" onclick="location.href='/config'">⚙ Config</button>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize matrix display with 32x16 grid
        function initializeMatrix() {
            const matrix = document.getElementById('matrix-display');
            matrix.innerHTML = '';
            
            for (let i = 0; i < 64 * 32; i++) {
                const pixel = document.createElement('div');
                pixel.className = 'pixel';
                pixel.id = `pixel-${i}`;
                matrix.appendChild(pixel);
            }
        }
        
        // Update pixel with color
        function setPixel(x, y, r, g, b) {
            if (x < 0 || x >= 64 || y < 0 || y >= 32) return;

            const index = y * 64 + x;
            const pixel = document.getElementById(`pixel-${index}`);
            
            if (pixel) {
                if (r > 10 || g > 10 || b > 10) {
                    pixel.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
                    pixel.classList.add('active');
                } else {
                    pixel.style.backgroundColor = '#0a0a0a';
                    pixel.classList.remove('active');
                }
            }
        }
        
        // Fetch and display current frame
        function updateDisplay() {
            fetch('/api/display')
                .then(response => response.json())
                .then(data => {
                    if (data.frame_data) {
                        // data.frame_data is base64 encoded image
                        const img = new Image();
                        img.onload = function() {
                            const canvas = document.createElement('canvas');
                            canvas.width = 64;
                            canvas.height = 32;
                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(img, 0, 0, 64, 32);

                            const imageData = ctx.getImageData(0, 0, 64, 32);
                            const data = imageData.data;
                            
                            // Update each pixel
                            for (let i = 0; i < 64 * 32; i++) {
                                const r = data[i * 4];
                                const g = data[i * 4 + 1];
                                const b = data[i * 4 + 2];
                                
                                const x = i % 64;
                                const y = Math.floor(i / 64);
                                setPixel(x, y, r, g, b);
                            }
                        };
                        img.src = 'data:image/png;base64,' + data.frame_data;
                    }
                    
                    if (data.current_app) {
                        document.getElementById('current-app').textContent = '▶️ ' + data.current_app;
                    }
                })
                .catch(error => console.error('Error updating display:', error));
        }
        
        // Load apps on page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeMatrix();
            loadApps();
            
            // Update display every 1000ms
            setInterval(updateDisplay, 1000);
            
            // Setup brightness slider
            const brightnessInput = document.getElementById('brightness');
            brightnessInput.addEventListener('input', function(e) {
                const value = e.target.value;
                document.getElementById('brightness-value').textContent = value + '%';
                setBrightness(value);
            });
        });
        
        function loadApps() {
            fetch('/api/apps')
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('apps-grid');
                    grid.innerHTML = '';
                    
                    data.apps.forEach(app => {
                        const card = document.createElement('div');
                        card.className = 'app-card' + (app.enabled ? '' : ' disabled');
                        card.innerHTML = `
                            <div class="app-name">${app.name}</div>
                            <div class="app-toggle">
                                <label class="toggle-switch">
                                    <input type="checkbox" ${app.enabled ? 'checked' : ''} 
                                           onchange="toggleApp('${app.name}', this.checked)">
                                    <span class="toggle-slider"></span>
                                </label>
                                <span>${app.enabled ? 'Enabled' : 'Disabled'}</span>
                            </div>
                        `;
                        grid.appendChild(card);
                    });
                    
                    // Update brightness
                    document.getElementById('brightness').value = data.brightness;
                    document.getElementById('brightness-value').textContent = data.brightness + '%';
                })
                .catch(error => {
                    console.error('Error loading apps:', error);
                    document.getElementById('status').textContent = 'Error';
                    document.getElementById('status').className = 'status-error';
                });
        }
        
        function toggleApp(appName, enabled) {
            fetch('/api/app/' + appName, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            })
            .then(() => loadApps())
            .catch(error => console.error('Error:', error));
        }
        
        function setBrightness(value) {
            fetch('/api/brightness', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({brightness: parseInt(value)})
            })
            .catch(error => console.error('Error:', error));
        }
        
        function saveConfig() {
            fetch('/api/config', {method: 'POST'})
                .then(() => alert('✅ Configuration saved!'))
                .catch(error => alert('❌ Error saving config'));
        }
        
        function reloadApps() {
            loadApps();
            updateDisplay();
        }
    </script>
</body>
</html>
"""


CONFIG_EDITOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tidbyt Config Editor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: 30px 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 700px;
            padding: 35px;
        }
        .header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        .back-btn {
            background: #f0f3ff;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            color: #667eea;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.95em;
            flex-shrink: 0;
        }
        .back-btn:hover { background: #e0e7ff; }
        h1 { color: #333; font-size: 1.8em; }
        .hint {
            color: #888;
            font-size: 0.88em;
            margin-bottom: 18px;
            line-height: 1.5;
        }
        .hint code {
            background: #f0f3ff;
            color: #667eea;
            padding: 1px 5px;
            border-radius: 4px;
            font-size: 0.95em;
        }
        textarea {
            width: 100%;
            height: 380px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            line-height: 1.6;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 16px;
            resize: vertical;
            outline: none;
            color: #222;
            background: #fafafa;
            transition: border-color 0.2s;
        }
        textarea:focus { border-color: #667eea; background: #fff; }
        textarea.error { border-color: #dc3545; }
        .btn-row {
            display: flex;
            gap: 10px;
            margin-top: 16px;
            align-items: center;
        }
        button {
            padding: 11px 22px;
            border: none;
            border-radius: 8px;
            font-size: 0.95em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:not(:disabled):hover { opacity: 0.9; transform: translateY(-1px); }
        .btn-secondary {
            background: #f0f3ff;
            color: #667eea;
        }
        .btn-secondary:hover { background: #e0e7ff; }
        .status {
            margin-left: auto;
            font-size: 0.9em;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 6px;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error   { background: #f8d7da; color: #721c24; }
        .status.warning { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <button class="back-btn" onclick="location.href='/'">← Back</button>
            <h1>Config Editor</h1>
        </div>
        <p class="hint">
            Edit the JSON directly and click <strong>Save &amp; Apply</strong>.
            Changes take effect immediately — no restart needed.<br>
            To change weather location set <code>"zip_code"</code>.
            To change stocks edit the <code>"symbols"</code> list.
        </p>

        <textarea id="editor" spellcheck="false"></textarea>

        <div class="btn-row">
            <button class="btn-primary" id="save-btn" onclick="saveConfig()">Save &amp; Apply</button>
            <button class="btn-secondary" onclick="formatJson()">Format JSON</button>
            <button class="btn-secondary" onclick="loadConfig()">Reload</button>
            <span class="status" id="status" style="display:none"></span>
        </div>
    </div>

    <script>
        function showStatus(msg, type) {
            const s = document.getElementById('status');
            s.textContent = msg;
            s.className = 'status ' + type;
            s.style.display = '';
            if (type === 'success') setTimeout(() => s.style.display = 'none', 4000);
        }

        function loadConfig() {
            fetch('/api/config/raw')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('editor').value = JSON.stringify(data, null, 2);
                    document.getElementById('editor').classList.remove('error');
                })
                .catch(e => showStatus('Failed to load config', 'error'));
        }

        function formatJson() {
            const ta = document.getElementById('editor');
            try {
                ta.value = JSON.stringify(JSON.parse(ta.value), null, 2);
                ta.classList.remove('error');
            } catch(e) {
                ta.classList.add('error');
                showStatus('Invalid JSON: ' + e.message, 'error');
            }
        }

        function saveConfig() {
            const ta = document.getElementById('editor');
            let parsed;
            try {
                parsed = JSON.parse(ta.value);
                ta.classList.remove('error');
            } catch(e) {
                ta.classList.add('error');
                showStatus('Invalid JSON: ' + e.message, 'error');
                return;
            }
            const btn = document.getElementById('save-btn');
            btn.disabled = true;
            btn.textContent = 'Applying...';
            fetch('/api/config/raw', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({config: ta.value})
            })
            .then(r => r.json())
            .then(d => {
                btn.disabled = false;
                btn.textContent = 'Save & Apply';
                if (d.success) {
                    showStatus(d.warning || 'Applied!', d.warning ? 'warning' : 'success');
                    loadConfig();
                } else {
                    showStatus('Error: ' + (d.error || 'unknown'), 'error');
                }
            })
            .catch(() => {
                btn.disabled = false;
                btn.textContent = 'Save & Apply';
                showStatus('Request failed', 'error');
            });
        }

        loadConfig();
    </script>
</body>
</html>
"""


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template_string(INDEX_TEMPLATE)


@app.route('/api/display', methods=['GET'])
def get_display():
    """Get current display frame as base64 encoded image"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    
    try:
        # Get the current image from the matrix
        current_image = tidbyt_display.display.current_image
        
        # Convert to PNG and encode as base64
        buffer = BytesIO()
        current_image.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Get current app name
        current_app = tidbyt_display.app_manager.get_current_app()
        app_name = current_app.name if current_app else "None"
        
        return jsonify({
            "frame_data": img_base64,
            "current_app": app_name,
            "width": 64,
            "height": 32
        })
    
    except Exception as e:
        print(f"Error getting display: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/apps', methods=['GET'])
def get_apps():
    """Get list of all apps and their status"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    
    apps = []
    for app in tidbyt_display.app_manager.apps:
        apps.append({
            "name": app.name,
            "enabled": app.is_enabled(),
            "priority": app.config.priority
        })
    
    return jsonify({
        "apps": apps,
        "brightness": tidbyt_display.display.get_brightness()
    })


@app.route('/api/app/<app_name>', methods=['POST'])
def update_app(app_name):
    """Enable or disable an app"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    
    data = request.json
    enabled = data.get('enabled', False)
    
    if enabled:
        tidbyt_display.enable_app(app_name)
    else:
        tidbyt_display.disable_app(app_name)
    
    return jsonify({"success": True})


@app.route('/api/brightness', methods=['POST'])
def set_brightness():
    """Set display brightness"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    
    data = request.json
    brightness = data.get('brightness', 100)
    tidbyt_display.set_brightness(brightness)
    
    return jsonify({"success": True})


@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500

    tidbyt_display.save_config()
    return jsonify({"success": True})


@app.route('/api/debug')
def debug_info():
    """Return diagnostic info about all apps"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    apps = []
    for app_obj in tidbyt_display.app_manager.apps:
        entry = {
            "name": app_obj.name,
            "enabled": app_obj.is_enabled(),
            "cached_frames": len(app_obj.cached_frames),
            "last_refresh": app_obj.last_refresh,
            "config": app_obj.config.config,
        }
        if app_obj.name == 'Weather':
            entry['lat'] = app_obj.lat
            entry['lon'] = app_obj.lon
            entry['location_name'] = app_obj.location_name
        apps.append(entry)
    current = tidbyt_display.app_manager.get_current_app()
    return jsonify({
        "apps": apps,
        "current_app": current.name if current else None,
        "config_path": tidbyt_display.config_path,
    })


@app.route('/config')
def config_editor():
    """Serve the config editor page"""
    return render_template_string(CONFIG_EDITOR_TEMPLATE)


@app.route('/api/config/raw', methods=['GET'])
def get_raw_config():
    """Return full config (including disabled apps) as JSON"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    # Return the stored config which includes all apps (enabled and disabled)
    config = dict(tidbyt_display._raw_config)
    config['brightness'] = tidbyt_display.display.get_brightness()
    return jsonify(config)


@app.route('/api/config/raw', methods=['POST'])
def save_raw_config():
    """Parse, apply, and persist a new config JSON"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500
    data = request.json or {}
    config_str = data.get('config', '')
    try:
        new_config = json.loads(config_str)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"success": False, "error": f"Invalid JSON: {e}"}), 400

    # Apply to running display — re-creates all app instances with new config
    try:
        tidbyt_display._apply_config(new_config)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

    # Persist to disk — try main path, then delete-and-recreate, then /tmp fallback
    config_path = tidbyt_display.config_path
    fallback_path = '/tmp/tidbyt_config.json'
    for path in [config_path, fallback_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
            with open(path, 'w') as f:
                json.dump(new_config, f, indent=2)
            if path != config_path:
                tidbyt_display.config_path = path
                return jsonify({"success": True, "warning":
                    f"Config applied! Saved to {path} because {config_path} is not writable. "
                    f"Fix with: sudo rm {config_path}"})
            return jsonify({"success": True})
        except Exception:
            continue
    return jsonify({"success": True, "warning": "Config applied but could not be saved to disk"})


# ============================================================================
# STARTUP
# ============================================================================

def start_display():
    """Start the Tidbyt display in a separate thread"""
    global tidbyt_display
    tidbyt_display = TidbytDisplay()
    tidbyt_display.start()


if __name__ == '__main__':
    # Start display in background thread
    display_thread = threading.Thread(target=start_display, daemon=True)
    display_thread.start()
    
    # Wait for display to initialize
    import time
    time.sleep(1)
    
    # Start web server
    print("Starting Tidbyt Web Dashboard...")
    print("Open http://localhost:5000 in your browser")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if tidbyt_display:
            tidbyt_display.stop()
