"""Red Sox MLB scores via statsapi.mlb.com"""

import time
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


class RedSoxApp(MatrixApp):
    """Shows today's Red Sox game score or schedule"""

    TEAM_ID = 111  # Boston Red Sox

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("RedSox", config)
        self._is_live = False

    def _fetch_game(self):
        """Fetch today's Red Sox game from MLB Stats API."""
        today = datetime.now().strftime("%Y-%m-%d")
        url = (
            f"https://statsapi.mlb.com/api/v1/schedule"
            f"?teamId={self.TEAM_ID}&sportId=1&date={today}"
            f"&hydrate=linescore"
        )
        try:
            resp = requests.get(url, timeout=8)
            data = resp.json()
        except Exception as e:
            print(f"RedSox API error: {e}")
            return None

        dates = data.get('dates', [])
        if not dates or not dates[0].get('games'):
            return None

        game = dates[0]['games'][0]
        status_code = game.get('status', {}).get('codedGameState', 'S')
        home_team = game.get('teams', {}).get('home', {})
        away_team = game.get('teams', {}).get('away', {})

        home_name = home_team.get('team', {}).get('name', 'Home')
        away_name = away_team.get('team', {}).get('name', 'Away')
        home_score = home_team.get('score', 0) or 0
        away_score = away_team.get('score', 0) or 0

        # Determine opponent (non-Red Sox side)
        home_id = home_team.get('team', {}).get('id', 0)
        if home_id == self.TEAM_ID:
            sox_score = home_score
            opp_score = away_score
            opp_name = away_name
            is_home = True
        else:
            sox_score = away_score
            opp_score = home_score
            opp_name = home_name
            is_home = False

        linescore = game.get('linescore', {})
        inning = linescore.get('currentInning', 0)
        inning_half = linescore.get('inningHalf', '')

        # Scheduled game time
        game_time = game.get('gameDate', '')
        try:
            dt = datetime.strptime(game_time, "%Y-%m-%dT%H:%M:%SZ")
            # Convert UTC to Eastern (rough -5h, -4h during DST — use simple offset)
            local_hour = (dt.hour - 5) % 24
            ampm = 'PM' if local_hour >= 12 else 'AM'
            display_hour = local_hour % 12 or 12
            display_time = f"{display_hour}:{dt.strftime('%M')} {ampm}"
        except Exception:
            display_time = "TBD"

        return {
            'status': status_code,
            'sox_score': sox_score,
            'opp_score': opp_score,
            'opp_name': opp_name,
            'is_home': is_home,
            'inning': inning,
            'inning_half': inning_half,
            'game_time': display_time,
        }

    def _abbrev(self, name: str, length: int = 8) -> str:
        """Abbreviate team name to fit display."""
        parts = name.split()
        if len(parts) >= 2 and len(name) > length:
            return parts[-1][:length]
        return name[:length]

    def get_frames(self) -> List[Image.Image]:
        frames = []
        try:
            font_title = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
            font_score = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
            font_status = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
        except Exception:
            font_title = font_score = font_status = ImageFont.load_default()

        game = self._fetch_game()

        if not game:
            self._is_live = False
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 5), "RED SOX", fill=(200, 20, 20), font=font_title)
            draw.text((2, 18), "No game", fill=(150, 150, 150), font=font_title)
            return [img] * 6

        status = game['status']
        self._is_live = (status == 'I')

        opp_abbr = self._abbrev(game['opp_name'])
        vs_label = f"vs {opp_abbr}" if game['is_home'] else f"@ {opp_abbr}"

        # Slide 1: RED SOX + opponent (6 frames)
        for _ in range(6):
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 2), "RED SOX", fill=(200, 20, 20), font=font_title)
            draw.text((2, 16), vs_label, fill=(180, 180, 180), font=font_title)
            frames.append(img)

        # Slide 2: Score (6 frames)
        score_str = f"{game['sox_score']} - {game['opp_score']}"
        for _ in range(6):
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), score_str, font=font_score)
            x = (64 - (bbox[2] - bbox[0])) // 2
            y = (32 - (bbox[3] - bbox[1])) // 2
            sox_color = (100, 255, 100) if game['sox_score'] >= game['opp_score'] else (255, 100, 100)
            draw.text((x, y), score_str, fill=sox_color, font=font_score)
            frames.append(img)

        # Slide 3: Status (6 frames)
        if status == 'F':
            status_str = "Final"
        elif status == 'I':
            half = "Top" if game['inning_half'].lower().startswith('top') else "Bot"
            status_str = f"{half} {game['inning']}"
        else:
            status_str = game['game_time']

        for _ in range(6):
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), status_str, font=font_status)
            x = (64 - (bbox[2] - bbox[0])) // 2
            draw.text((x, 10), status_str, fill=(200, 200, 100), font=font_status)
            frames.append(img)

        return frames

    def needs_refresh(self) -> bool:
        interval = 60 if self._is_live else 600
        return time.time() - self.last_refresh > interval
