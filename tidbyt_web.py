#!/usr/bin/env python3
"""
Web UI for Tidbyt Display Control
Flask-based dashboard for managing apps and display settings
Includes emulated 32x16 matrix display
"""

import json
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
                <button class="btn-secondary" onclick="location.href='/settings'">⚙ Settings</button>
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


SETTINGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tidbyt Settings</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: 40px 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
        }
        .header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
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
        }
        .back-btn:hover { background: #e0e7ff; }
        h1 { color: #333; font-size: 2em; }
        .section { margin-bottom: 35px; }
        .section-title {
            color: #667eea;
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #f0f0f0;
        }
        label { display: block; color: #555; margin-bottom: 6px; font-size: 0.95em; }
        input[type="text"] {
            width: 100%;
            padding: 10px 14px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1em;
            outline: none;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus { border-color: #667eea; }
        .symbol-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
            min-height: 36px;
        }
        .symbol-tag {
            background: #f0f3ff;
            border: 1px solid #c0c8f0;
            color: #333;
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 0.9em;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .symbol-tag .remove {
            cursor: pointer;
            color: #999;
            font-weight: bold;
            line-height: 1;
        }
        .symbol-tag .remove:hover { color: #e74c3c; }
        .add-row {
            display: flex;
            gap: 8px;
        }
        .add-row input { flex: 1; }
        button {
            padding: 10px 18px;
            border: none;
            border-radius: 8px;
            font-size: 0.95em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn-small {
            background: #667eea;
            color: white;
            padding: 8px 14px;
            font-size: 0.9em;
        }
        .save-row { margin-top: 12px; }
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 12px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            font-size: 0.95em;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }
        .toast.show { opacity: 1; }
        .toast.success { background: #28a745; }
        .toast.error { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <button class="back-btn" onclick="location.href='/'">← Back</button>
            <h1>Settings</h1>
        </div>

        <!-- Weather Settings -->
        <div class="section">
            <div class="section-title">Weather</div>
            <label for="zip-code">Zip Code</label>
            <input type="text" id="zip-code" placeholder="e.g. 02134" maxlength="10">
            <div class="save-row">
                <button class="btn-primary" onclick="saveWeather()">Save Weather</button>
            </div>
        </div>

        <!-- Stocks Settings -->
        <div class="section">
            <div class="section-title">Stocks</div>
            <label>Symbols</label>
            <div class="symbol-list" id="symbol-list"></div>
            <div class="add-row">
                <input type="text" id="new-symbol" placeholder="e.g. NVDA" maxlength="10"
                       onkeydown="if(event.key==='Enter') addStock()">
                <button class="btn-small" onclick="addStock()">Add</button>
            </div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        let currentSymbols = [];

        function showToast(msg, type) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = 'toast ' + type + ' show';
            setTimeout(() => t.className = 'toast', 2500);
        }

        function renderSymbols() {
            const list = document.getElementById('symbol-list');
            list.innerHTML = '';
            currentSymbols.forEach(sym => {
                const tag = document.createElement('div');
                tag.className = 'symbol-tag';
                tag.innerHTML = sym + '<span class="remove" onclick="removeStock(\'' + sym + '\')">✕</span>';
                list.appendChild(tag);
            });
        }

        function addStock() {
            const input = document.getElementById('new-symbol');
            const sym = input.value.trim().toUpperCase();
            if (!sym) return;
            if (currentSymbols.includes(sym)) { showToast(sym + ' already in list', 'error'); return; }
            currentSymbols.push(sym);
            input.value = '';
            renderSymbols();
            saveStocks();
        }

        function removeStock(sym) {
            currentSymbols = currentSymbols.filter(s => s !== sym);
            renderSymbols();
            saveStocks();
        }

        function saveWeather() {
            const zip = document.getElementById('zip-code').value.trim();
            if (!zip) { showToast('Please enter a zip code', 'error'); return; }
            fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({weather: {zip_code: zip}})
            })
            .then(r => r.json())
            .then(d => d.success ? showToast('Weather saved!', 'success') : showToast('Error saving', 'error'))
            .catch(() => showToast('Error saving', 'error'));
        }

        function saveStocks() {
            fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({stocks: {symbols: currentSymbols}})
            })
            .then(r => r.json())
            .then(d => { if (d.success) showToast('Stocks saved!', 'success'); })
            .catch(() => showToast('Error saving stocks', 'error'));
        }

        // Load current settings
        fetch('/api/settings')
            .then(r => r.json())
            .then(data => {
                document.getElementById('zip-code').value = data.weather?.zip_code || '';
                currentSymbols = data.stocks?.symbols || [];
                renderSymbols();
            })
            .catch(e => console.error('Error loading settings:', e));
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


@app.route('/settings')
def settings_page():
    """Serve the settings page"""
    return render_template_string(SETTINGS_TEMPLATE)


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Return current app-specific settings (zip_code, symbols)"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500

    result = {}
    for app_obj in tidbyt_display.app_manager.apps:
        if app_obj.name == 'Weather':
            result['weather'] = {'zip_code': app_obj.config.config.get('zip_code', '02134')}
        elif app_obj.name == 'Stocks':
            result['stocks'] = {'symbols': app_obj.config.config.get('symbols', [])}
    return jsonify(result)


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update app-specific settings live and persist to disk"""
    if not tidbyt_display:
        return jsonify({"error": "Display not initialized"}), 500

    data = request.json or {}

    for app_obj in tidbyt_display.app_manager.apps:
        if app_obj.name == 'Weather' and 'weather' in data:
            new_zip = data['weather'].get('zip_code')
            if new_zip:
                app_obj.config.config['zip_code'] = new_zip
                app_obj.zip_code = new_zip
                app_obj._resolve_location()
                app_obj.last_refresh = 0  # force refresh
        elif app_obj.name == 'Stocks' and 'stocks' in data:
            new_symbols = data['stocks'].get('symbols')
            if new_symbols is not None:
                app_obj.config.config['symbols'] = new_symbols
                app_obj.symbols = new_symbols
                app_obj.last_refresh = 0  # force refresh

    tidbyt_display.save_config()
    return jsonify({"success": True})


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
