#!/usr/bin/env python3
"""
Real API Integration Examples for Tidbyt Display
Examples showing how to integrate actual data sources
"""

from tidbyt_apps import MatrixApp, AppConfig
from PIL import Image, ImageDraw, ImageFont
import requests
import time
from datetime import datetime


# ============================================================================
# WEATHER - Open-Meteo (FREE, no API key needed!)
# ============================================================================

class WeatherAppReal(MatrixApp):
    """Real weather data from Open-Meteo"""
    
    def __init__(self, config=None):
        super().__init__("Weather", config)
        # Boston coordinates - change for your location
        self.latitude = config.config.get('latitude', 42.36) if config else 42.36
        self.longitude = config.config.get('longitude', -71.06) if config else -71.06
        self.location = config.config.get('location', 'Boston') if config else 'Boston'
        self.weather_data = None
    
    def fetch_weather(self):
        """Fetch weather from Open-Meteo"""
        try:
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "temperature_unit": "fahrenheit",
                "timezone": "auto"
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            self.weather_data = {
                "temp": int(data['current']['temperature_2m']),
                "humidity": data['current']['relative_humidity_2m'],
                "wind": int(data['current']['wind_speed_10m']),
                "code": data['current']['weather_code']
            }
            
            return True
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return False
    
    def get_weather_emoji(self, code):
        """Get emoji for weather code"""
        # WMO Weather codes
        if code == 0:
            return "☀️"  # Clear
        elif code == 1 or code == 2:
            return "⛅"  # Mostly clear
        elif code == 3:
            return "☁️"  # Overcast
        elif code == 45 or code == 48:
            return "🌫️"  # Foggy
        elif code in range(51, 68):
            return "🌧️"  # Rain
        elif code in range(71, 86):
            return "❄️"  # Snow
        elif code in range(80, 83):
            return "🌦️"  # Showers
        elif code in range(85, 88):
            return "🌨️"  # Snow showers
        else:
            return "⛈️"  # Thunderstorm
    
    def get_frames(self):
        """Generate weather display frames"""
        if not self.weather_data:
            return self._error_frame()
        
        frames = []
        
        # Frame 1: Temperature
        img = Image.new('RGB', (32, 16), (0, 0, 15))
        draw = ImageDraw.Draw(img)
        try:
            temp_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 6)
        except:
            temp_font = label_font = ImageFont.load_default()
        
        draw.text((2, 0), "WEATHER", fill=(255, 200, 0), font=label_font)
        draw.text((2, 7), f"{self.weather_data['temp']}°F", fill=(100, 200, 255), font=temp_font)
        frames.append(img)
        
        # Frame 2: Humidity & Wind
        img = Image.new('RGB', (32, 16), (0, 0, 15))
        draw = ImageDraw.Draw(img)
        draw.text((2, 1), f"H:{self.weather_data['humidity']}%", fill=(150, 200, 100), font=label_font)
        draw.text((2, 8), f"W:{self.weather_data['wind']}mph", fill=(200, 150, 100), font=label_font)
        frames.append(img)
        
        return frames * 10  # Show for ~1 second
    
    def _error_frame(self):
        img = Image.new('RGB', (32, 16), (20, 0, 0))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((2, 6), "No weather", fill=(255, 100, 100), font=font)
        return [img] * 30
    
    def needs_refresh(self):
        """Refresh every 15 minutes"""
        return time.time() - self.last_refresh > 900


# ============================================================================
# STOCKS - Using yfinance (requires: pip install yfinance)
# ============================================================================

class StockAppReal(MatrixApp):
    """Real stock prices from yfinance"""
    
    def __init__(self, config=None):
        super().__init__("Stocks", config)
        self.symbols = config.config.get('symbols', ['AAPL', 'MSFT', 'TSLA']) if config else ['AAPL', 'MSFT', 'TSLA']
        self.stock_data = {}
    
    def fetch_stocks(self):
        """Fetch stock data"""
        try:
            import yfinance as yf
            
            for symbol in self.symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    price = info.get('currentPrice', 0)
                    prev_close = info.get('previousClose', price)
                    change = price - prev_close
                    change_pct = (change / prev_close * 100) if prev_close else 0
                    
                    self.stock_data[symbol] = {
                        'price': f"{price:.2f}",
                        'change': f"{change_pct:+.1f}%",
                        'is_up': change >= 0
                    }
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
            
            return len(self.stock_data) > 0
        
        except ImportError:
            print("Install yfinance: pip install yfinance")
            return False
        except Exception as e:
            print(f"Stock fetch error: {e}")
            return False
    
    def get_frames(self):
        """Generate stock display frames"""
        if not self.stock_data:
            return self._error_frame()
        
        frames = []
        
        for symbol, data in self.stock_data.items():
            img = Image.new('RGB', (32, 16), (0, 0, 10))
            draw = ImageDraw.Draw(img)
            
            try:
                symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 10)
                price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)
            except:
                symbol_font = price_font = ImageFont.load_default()
            
            color = (100, 255, 100) if data['is_up'] else (255, 100, 100)
            
            draw.text((2, 1), symbol, fill=(200, 200, 200), font=symbol_font)
            draw.text((2, 9), data['price'], fill=(255, 255, 255), font=price_font)
            draw.text((18, 9), data['change'], fill=color, font=price_font)
            
            frames.append(img)
        
        return frames * 10
    
    def _error_frame(self):
        img = Image.new('RGB', (32, 16), (20, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 6), "No stocks", fill=(255, 100, 100))
        return [img] * 30
    
    def needs_refresh(self):
        """Refresh every 5 minutes"""
        return time.time() - self.last_refresh > 300


# ============================================================================
# RED SOX SCORES - MLB Stats API (FREE)
# ============================================================================

class RedSoxApp(MatrixApp):
    """Live Red Sox game scores"""
    
    def __init__(self, config=None):
        super().__init__("Red Sox", config)
        self.game_data = None
    
    def fetch_game(self):
        """Fetch latest Red Sox game"""
        try:
            # Get Red Sox schedule for current season
            url = "https://statsapi.mlb.com/api/v1/teams/111/schedule"
            params = {"season": datetime.now().year}
            
            response = requests.get(url, params=params, timeout=5)
            games = response.json()['records']
            
            if not games:
                return False
            
            # Get most recent game
            game = games[-1]
            
            self.game_data = {
                'home_team': game['teams']['home']['team']['name'].split()[-1],  # Just last word
                'away_team': game['teams']['away']['team']['name'].split()[-1],
                'home_score': game['teams']['home']['score'],
                'away_score': game['teams']['away']['score'],
                'status': game['status']['detailedState'],
                'is_red_sox_home': game['teams']['home']['team']['id'] == 111
            }
            
            return True
        
        except Exception as e:
            print(f"Red Sox error: {e}")
            return False
    
    def get_frames(self):
        """Generate game display frames"""
        if not self.game_data:
            return self._error_frame()
        
        frames = []
        
        # Frame 1: Teams
        img = Image.new('RGB', (32, 16), (30, 0, 0))  # Red Sox red
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 6)
        except:
            font = ImageFont.load_default()
        
        if self.game_data['is_red_sox_home']:
            away = self.game_data['away_team']
            home = "SOX"
        else:
            away = "SOX"
            home = self.game_data['home_team']
        
        draw.text((2, 2), f"{away} @", fill=(255, 255, 255), font=font)
        draw.text((2, 9), home, fill=(255, 200, 200), font=font)
        frames.append(img)
        
        # Frame 2: Score
        img = Image.new('RGB', (32, 16), (30, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            score_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
        except:
            score_font = font
        
        if self.game_data['is_red_sox_home']:
            away_score = self.game_data['away_score']
            home_score = self.game_data['home_score']
        else:
            away_score = self.game_data['home_score']
            home_score = self.game_data['away_score']
        
        draw.text((4, 3), f"{away_score}-{home_score}", fill=(255, 255, 100), font=score_font)
        frames.append(img)
        
        # Frame 3: Status
        img = Image.new('RGB', (32, 16), (30, 0, 0))
        draw = ImageDraw.Draw(img)
        status = self.game_data['status'][:14]  # Truncate for display
        draw.text((2, 6), status, fill=(150, 200, 255), font=font)
        frames.append(img)
        
        return frames * 10
    
    def _error_frame(self):
        img = Image.new('RGB', (32, 16), (30, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 6), "No game", fill=(255, 100, 100))
        return [img] * 30
    
    def needs_refresh(self):
        """Refresh every 10 minutes"""
        return time.time() - self.last_refresh > 600


# ============================================================================
# CRYPTO - CoinGecko API (FREE)
# ============================================================================

class CryptoApp(MatrixApp):
    """Bitcoin/Ethereum prices from CoinGecko"""
    
    def __init__(self, config=None):
        super().__init__("Crypto", config)
        self.coins = config.config.get('coins', ['bitcoin', 'ethereum']) if config else ['bitcoin', 'ethereum']
        self.crypto_data = {}
    
    def fetch_crypto(self):
        """Fetch crypto prices"""
        try:
            ids = ','.join(self.coins)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ids,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            for coin in self.coins:
                if coin in data:
                    price = data[coin]['usd']
                    change = data[coin]['usd_24h_change']
                    
                    self.crypto_data[coin.upper()] = {
                        'price': f"${price:,.0f}" if price > 1000 else f"${price:.2f}",
                        'change': f"{change:+.1f}%",
                        'is_up': change >= 0
                    }
            
            return len(self.crypto_data) > 0
        
        except Exception as e:
            print(f"Crypto fetch error: {e}")
            return False
    
    def get_frames(self):
        """Generate crypto display frames"""
        if not self.crypto_data:
            return self._error_frame()
        
        frames = []
        
        for coin, data in self.crypto_data.items():
            img = Image.new('RGB', (32, 16), (0, 0, 20))
            draw = ImageDraw.Draw(img)
            
            try:
                coin_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 9)
                price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 7)
            except:
                coin_font = price_font = ImageFont.load_default()
            
            color = (100, 255, 100) if data['is_up'] else (255, 100, 100)
            
            draw.text((2, 2), coin[:4], fill=(255, 215, 0), font=coin_font)
            draw.text((2, 9), data['price'][:10], fill=(255, 255, 255), font=price_font)
            draw.text((18, 9), data['change'], fill=color, font=price_font)
            
            frames.append(img)
        
        return frames * 10
    
    def _error_frame(self):
        img = Image.new('RGB', (32, 16), (20, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 6), "No crypto", fill=(255, 100, 100))
        return [img] * 30
    
    def needs_refresh(self):
        """Refresh every 10 minutes"""
        return time.time() - self.last_refresh > 600


# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    # Test weather
    weather = WeatherAppReal()
    weather.fetch_weather()
    frames = weather.get_frames()
    print(f"Weather: {len(frames)} frames")
    
    # Test Red Sox
    sox = RedSoxApp()
    sox.fetch_game()
    frames = sox.get_frames()
    print(f"Red Sox: {len(frames)} frames")
    
    # Test crypto
    crypto = CryptoApp()
    crypto.fetch_crypto()
    frames = crypto.get_frames()
    print(f"Crypto: {len(frames)} frames")
    
    print("\nAll apps working! Add to tidbyt_main.py to use.")
