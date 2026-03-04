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

from tidbyt_matrix import MatrixDisplay, MatrixConfig
from tidbyt_apps import (
    AppManager, ClockApp, WeatherApp, StockApp, 
    ArtApp, NewsHeadlinesApp, AppConfig
)


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
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self._apply_config(config)
                print(f"Loaded config from {self.config_path}")
            except Exception as e:
                print(f"Error loading config: {e}")
                self._setup_default_config()
        else:
            self._setup_default_config()
    
    def _setup_default_config(self):
        """Setup default apps and configuration"""
        # Create default config
        default_config = {
            "brightness": 100,
            "apps": {
                "clock": {"enabled": True, "priority": 10},
                "weather": {"enabled": True, "priority": 5},
                "stocks": {"enabled": True, "priority": 5},
                "art": {"enabled": True, "priority": 1},
                "news": {"enabled": False, "priority": 3},
            }
        }
        
        # Save default config (best effort)
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
        
        self._apply_config(default_config)
    
    def _apply_config(self, config: dict):
        """Apply loaded configuration"""
        # Set brightness
        brightness = config.get('brightness', 100)
        self.display.set_brightness(brightness)
        
        # Setup apps based on config
        self._setup_apps(config.get('apps', {}))
    
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
                refresh_interval=600
            )
            self.app_manager.add_app(WeatherApp(weather_cfg))
        
        # Stocks app
        if apps_config.get('stocks', {}).get('enabled', True):
            stocks_cfg = AppConfig(
                enabled=True,
                priority=apps_config.get('stocks', {}).get('priority', 5),
                display_duration=10,
                refresh_interval=300
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
    
    def _display_loop(self):
        """Main display loop"""
        try:
            while self.is_running:
                with self.lock:
                    # Get current app
                    current_app = self.app_manager.get_current_app()
                    
                    if current_app:
                        # Refresh app data if needed
                        current_app.refresh()
                        
                        # Get frames for current app
                        frames = current_app.get_cached_frames()
                        
                        if frames:
                            # Cycle through frames
                            frame_idx = int((time.time() * 10) % len(frames))
                            self.display.draw_image(frames[frame_idx])
                        
                        # Check if we should rotate to next app
                        if self.app_manager.should_rotate():
                            self.app_manager.rotate_app()
                    
                    # Small sleep to prevent CPU spinning
                    time.sleep(0.1)
        
        except Exception as e:
            print(f"Error in display loop: {e}")
            import traceback
            traceback.print_exc()
    
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
        """Save current configuration"""
        config = {
            "brightness": self.display.get_brightness(),
            "apps": {}
        }
        
        for app in self.app_manager.apps:
            config["apps"][app.name.lower()] = {
                "enabled": app.is_enabled(),
                "priority": app.config.priority
            }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Config saved to {self.config_path}")


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
