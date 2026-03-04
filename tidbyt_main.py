#!/usr/bin/env python3
"""
Main Tidbyt Display Controller
Manages app cycling, display updates, and system control
"""

import time
import threading
import json
import os
from datetime import datetime
from typing import Optional, List
import signal
import sys
from PIL import Image

from tidbyt_matrix import MatrixDisplay, MatrixConfig
from tidbyt_apps import (
    AppManager, ClockApp, WeatherApp, StockApp,
    ArtApp, NewsHeadlinesApp, AppConfig
)
from apps.clock_custom import CustomClockApp
from apps.countdown_app import CountdownApp
from apps.weather_animated import WeatherAnimatedApp
from apps.redsox_app import RedSoxApp


class TidbytDisplay:
    """Main display controller"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tidbyt_config.json")
        """Initialize Tidbyt display"""
        self.config_path = config_path
        self.display = MatrixDisplay(MatrixConfig())
        self.app_manager = AppManager()
        self.is_running = False
        self.current_frame_index = 0
        self.current_app_frames = []
        self.app_start_time = time.time()
        
        # Lock for thread-safe operations
        self.lock = threading.Lock()

        # Full config dict (including disabled apps) — used by web config editor
        self._raw_config = {}

        # Seconds each frame is displayed (1/fps). 0.5 = 2fps, 1.0 = 1fps
        self.frame_delay = 0.5

        # Display power state — always starts OFF (display stays dark until manually enabled)
        self.display_enabled = False

        # Horizontal scroll transition state
        self._transition_frames = []
        self._transition_idx = 0
        
        # Load configuration
        self.load_config()
        
        # Setup signal handlers for graceful shutdown (main thread only)
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\nShutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def _write_config_to_disk(self, config: dict):
        """Atomically write config to the primary config path.

        Uses write-to-temp-then-rename so a failed write never corrupts or
        deletes the existing file.  config_path is NEVER changed to /tmp.
        Returns (success: bool, error_msg: str|None).
        """
        tmp_path = self.config_path + '.tmp'
        try:
            with open(tmp_path, 'w') as f:
                json.dump(config, f, indent=2)
            os.replace(tmp_path, self.config_path)
            print(f"Config saved to {self.config_path}")
            return True, None
        except PermissionError:
            # Likely the existing config file is owned by root from a previous
            # sudo run.  Delete it first — directory write permission is enough
            # for unlink — then recreate.
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            try:
                if os.path.exists(self.config_path):
                    os.remove(self.config_path)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"Config saved to {self.config_path} (replaced root-owned file)")
                return True, None
            except Exception as e2:
                msg = (f"Cannot write to {self.config_path}: {e2}. "
                       f"Run: sudo chown andy:andy {self.config_path}")
                print(f"Warning: {msg}")
                return False, msg
        except Exception as e:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            msg = f"Cannot write to {self.config_path}: {e}"
            print(f"Warning: {msg}")
            return False, msg

    def load_config(self):
        """Load configuration from file.

        Tries the primary path first.  Falls back to /tmp (left by a previous
        session) and migrates it to the primary path if found there.
        """
        candidates = [self.config_path, '/tmp/tidbyt_config.json']
        for path in candidates:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                self._apply_config(config)
                print(f"Loaded config from {path}")
                if path != self.config_path:
                    print(f"Migrating config from {path} → {self.config_path}")
                    self._write_config_to_disk(config)
                return
            except Exception as e:
                print(f"Error loading config from {path}: {e}")
        self._setup_default_config()

    def _setup_default_config(self):
        """Apply and persist factory defaults."""
        default_config = {"brightness": 100, "apps": {}}
        self._apply_config(default_config)
        ok, err = self._write_config_to_disk(self._raw_config)
        if not ok:
            print(f"Warning: Could not save default config: {err}")
    
    def _default_apps_config(self) -> dict:
        """Full default apps dict — used to ensure all keys are always present in stored config."""
        return {
            "clock":            {"enabled": True,  "priority": 10},
            "weather":          {"enabled": True,  "priority": 5,  "zip_code": "02134"},
            "stocks":           {"enabled": True,  "priority": 5,  "symbols": ["AAPL", "TSLA"]},
            "art":              {"enabled": True,  "priority": 1},
            "news":             {"enabled": False, "priority": 3},
            "clock_custom":     {"enabled": False, "priority": 9,  "color_theme": "blue", "format_24h": False},
            "countdown":        {"enabled": False, "priority": 4,  "events": [{"name": "Summer", "date": "2026-06-21"}]},
            "weather_animated": {"enabled": False, "priority": 6,  "zip_code": "02134"},
            "redsox":           {"enabled": False, "priority": 7},
        }

    def _apply_config(self, config: dict):
        """Apply loaded configuration"""
        # Merge incoming apps with defaults so newly-added apps always appear in the editor
        merged_apps = self._default_apps_config()
        merged_apps.update(config.get('apps', {}))
        merged = dict(config)
        merged['apps'] = merged_apps
        merged.setdefault('frame_delay', 0.5)

        # Store full config for the web config editor
        self._raw_config = merged

        # Frame delay — stored separately for use in display loop
        self.frame_delay = float(merged.get('frame_delay', 0.5))

        # Set brightness
        brightness = merged.get('brightness', 100)
        self.display.set_brightness(brightness)

        # Setup apps based on config
        self._setup_apps(merged_apps)
    
    def _setup_apps(self, apps_config: dict):
        """Setup apps from configuration"""
        self.app_manager = AppManager()
        
        # Clock app
        if apps_config.get('clock', {}).get('enabled', True):
            clock_cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('clock', {}).get('priority', 10),
                display_duration=10,
                refresh_interval=10
            )
            self.app_manager.add_app(ClockApp(clock_cfg))
        
        # Weather app
        if apps_config.get('weather', {}).get('enabled', True):
            weather_cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('weather', {}).get('priority', 5),
                display_duration=10,
                refresh_interval=600,
                config={
                    'zip_code': apps_config.get('weather', {}).get('zip_code', '02134')
                }
            )
            self.app_manager.add_app(WeatherApp(weather_cfg))

        # Stocks app
        if apps_config.get('stocks', {}).get('enabled', True):
            stocks_cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('stocks', {}).get('priority', 5),
                display_duration=10,
                refresh_interval=300,
                config={
                    'symbols': apps_config.get('stocks', {}).get('symbols', ['AAPL', 'TSLA'])
                }
            )
            self.app_manager.add_app(StockApp(stocks_cfg))
        
        # Art app
        if apps_config.get('art', {}).get('enabled', True):
            art_cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('art', {}).get('priority', 1),
                display_duration=8,
                refresh_interval=0
            )
            self.app_manager.add_app(ArtApp(art_cfg))
        
        # News app
        if apps_config.get('news', {}).get('enabled', False):
            news_cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('news', {}).get('priority', 3),
                display_duration=12,
                refresh_interval=1800
            )
            self.app_manager.add_app(NewsHeadlinesApp(news_cfg))

        # Custom Clock app
        if apps_config.get('clock_custom', {}).get('enabled', False):
            cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('clock_custom', {}).get('priority', 9),
                display_duration=12,
                refresh_interval=10,
                config={
                    'color_theme': apps_config.get('clock_custom', {}).get('color_theme', 'blue'),
                    'format_24h': apps_config.get('clock_custom', {}).get('format_24h', False),
                }
            )
            self.app_manager.add_app(CustomClockApp(cfg))

        # Countdown app
        if apps_config.get('countdown', {}).get('enabled', False):
            events = apps_config.get('countdown', {}).get('events', [{'name': 'Summer', 'date': '2026-06-21'}])
            cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('countdown', {}).get('priority', 4),
                display_duration=max(8, 8 * len(events)),
                refresh_interval=3600,
                config={'events': events}
            )
            self.app_manager.add_app(CountdownApp(cfg))

        # Animated Weather app
        if apps_config.get('weather_animated', {}).get('enabled', False):
            cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('weather_animated', {}).get('priority', 6),
                display_duration=10,
                refresh_interval=600,
                config={
                    'zip_code': apps_config.get('weather_animated', {}).get('zip_code', '02134'),
                }
            )
            self.app_manager.add_app(WeatherAnimatedApp(cfg))

        # Red Sox app
        if apps_config.get('redsox', {}).get('enabled', False):
            cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('redsox', {}).get('priority', 7),
                display_duration=9,
                refresh_interval=300
            )
            self.app_manager.add_app(RedSoxApp(cfg))

        print(f"Setup {len(self.app_manager.apps)} apps")
    
    def start(self):
        """Start the display"""
        self.is_running = True
        print("Starting Tidbyt display...")
        
        # Start display thread
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
    
    def stop(self):
        """Stop the display"""
        self.is_running = False
        self.display.clear()
        self.display.close()
        print("Display stopped")
    
    def _build_transition(self, frame_a: Image.Image, frame_b: Image.Image, steps: int = 16):
        """Build horizontal scroll frames: frame_b slides in from right, frame_a exits left."""
        frames = []
        for i in range(1, steps + 1):
            offset = int(i * 64 / steps)
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            if offset < 64:
                img.paste(frame_a.crop((offset, 0, 64, 32)), (0, 0))
            if offset > 0:
                img.paste(frame_b.crop((0, 0, min(offset, 64), 32)), (64 - offset, 0))
            frames.append(img)
        return frames

    def _display_loop(self):
        """Main display loop"""
        _display_was_on = False
        try:
            while self.is_running:
                # --- Display powered off ---
                if not self.display_enabled:
                    if _display_was_on:
                        with self.lock:
                            self.display.clear()
                        _display_was_on = False
                        self._transition_frames = []
                        self._transition_idx = 0
                    time.sleep(0.1)
                    continue
                _display_was_on = True

                with self.lock:
                    # --- Transition playback (runs at 20fps for smooth scroll) ---
                    if self._transition_frames:
                        self.display.draw_image(self._transition_frames[self._transition_idx])
                        self._transition_idx += 1
                        if self._transition_idx >= len(self._transition_frames):
                            self._transition_frames = []
                            self._transition_idx = 0
                        time.sleep(0.05)
                        continue

                    # --- Normal display ---
                    current_app = self.app_manager.get_current_app()

                    if current_app:
                        # Refresh app data if needed
                        current_app.refresh()

                        # Get frames for current app
                        frames = current_app.get_cached_frames()

                        current_frame = None
                        if frames:
                            frame_idx = int((time.time() / self.frame_delay) % len(frames))
                            current_frame = frames[frame_idx]
                            self.display.draw_image(current_frame)

                        # Check if we should rotate to next app
                        if self.app_manager.should_rotate():
                            self.app_manager.rotate_app()
                            # Build scroll transition if multiple apps are active
                            next_app = self.app_manager.get_current_app()
                            enabled = self.app_manager.get_enabled_apps()
                            if next_app and current_frame and len(enabled) > 1:
                                next_app.refresh()
                                next_frames = next_app.get_cached_frames()
                                if next_frames:
                                    self._transition_frames = self._build_transition(
                                        current_frame, next_frames[0])
                                    self._transition_idx = 0
                    else:
                        # No apps enabled — clear display
                        self.display.clear()

                    # Small sleep to prevent CPU spinning
                    time.sleep(0.1)
        
        except Exception as e:
            print(f"Error in display loop: {e}")
            import traceback
            traceback.print_exc()
    
    def set_display_power(self, on: bool):
        """Turn the LED matrix on or off without stopping the display thread"""
        self.display_enabled = on
        if not on:
            self.display.clear()

    def set_brightness(self, brightness: int):
        """Set display brightness"""
        self.display.set_brightness(brightness)
    
    def enable_app(self, app_name: str):
        """Enable an app"""
        for app in self.app_manager.apps:
            if app.name.lower() == app_name.lower():
                app.config.enabled = True
                print(f"Enabled {app_name}")
                return
    
    def disable_app(self, app_name: str):
        """Disable an app"""
        for app in self.app_manager.apps:
            if app.name.lower() == app_name.lower():
                app.config.enabled = False
                print(f"Disabled {app_name}")
                return
    
    def list_apps(self) -> List[str]:
        """Get list of available apps"""
        return [app.name for app in self.app_manager.apps]
    
    def save_config(self):
        """Save current configuration to disk."""
        config = dict(self._raw_config)
        config['brightness'] = self.display.get_brightness()
        self._write_config_to_disk(config)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

class CLI:
    """Command line interface for controlling display"""
    
    def __init__(self, tidbyt: TidbytDisplay):
        self.tidbyt = tidbyt
    
    def print_help(self):
        """Print help message"""
        print("""
Tidbyt Display Commands:
  list                    - List all apps
  enable <app>            - Enable an app
  disable <app>           - Disable an app
  brightness <0-100>      - Set brightness
  save                    - Save configuration
  help                    - Show this help
  exit                    - Exit the program
        """)
    
    def run(self):
        """Run the CLI"""
        self.print_help()
        
        try:
            while self.tidbyt.is_running:
                try:
                    cmd = input("> ").strip().lower()
                    
                    if not cmd:
                        continue
                    
                    parts = cmd.split()
                    command = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    
                    if command == 'list':
                        apps = self.tidbyt.list_apps()
                        print(f"Available apps: {', '.join(apps)}")
                    
                    elif command == 'enable' and args:
                        self.tidbyt.enable_app(args[0])
                    
                    elif command == 'disable' and args:
                        self.tidbyt.disable_app(args[0])
                    
                    elif command == 'brightness' and args:
                        try:
                            brightness = int(args[0])
                            self.tidbyt.set_brightness(brightness)
                            print(f"Brightness set to {brightness}")
                        except ValueError:
                            print("Invalid brightness value")
                    
                    elif command == 'save':
                        self.tidbyt.save_config()
                    
                    elif command == 'help':
                        self.print_help()
                    
                    elif command == 'exit':
                        break
                    
                    else:
                        print("Unknown command. Type 'help' for help.")
                
                except KeyboardInterrupt:
                    break
        
        finally:
            self.tidbyt.stop()


if __name__ == "__main__":
    # Create and start display
    tidbyt = TidbytDisplay()
    tidbyt.start()
    
    # Run CLI
    cli = CLI(tidbyt)
    cli.run()
