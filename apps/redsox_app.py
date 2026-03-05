"""Red Sox MLB split-screen scoreboard + standings via statsapi.mlb.com"""

import time
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from tidbyt_apps import MatrixApp, AppConfig
from typing import Optional, List


# All 30 MLB teams: id → {abbr, color}
TEAMS = {
    108: {"abbr": "LAA", "color": (186, 0, 33)},
    109: {"abbr": "ARI", "color": (167, 25, 48)},
    110: {"abbr": "BAL", "color": (223, 70, 1)},
    111: {"abbr": "BOS", "color": (200, 20, 20)},
    112: {"abbr": "CHC", "color": (14, 51, 134)},
    113: {"abbr": "CIN", "color": (198, 1, 31)},
    114: {"abbr": "CLE", "color": (0, 56, 168)},
    115: {"abbr": "COL", "color": (51, 0, 111)},
    116: {"abbr": "DET", "color": (12, 35, 64)},
    117: {"abbr": "HOU", "color": (0, 45, 98)},
    118: {"abbr": "KC",  "color": (0, 70, 135)},
    119: {"abbr": "LAD", "color": (0, 90, 156)},
    120: {"abbr": "WSH", "color": (171, 0, 3)},
    121: {"abbr": "NYM", "color": (0, 45, 114)},
    133: {"abbr": "OAK", "color": (0, 56, 49)},
    134: {"abbr": "PIT", "color": (253, 184, 39)},
    135: {"abbr": "SD",  "color": (47, 36, 28)},
    136: {"abbr": "SEA", "color": (0, 92, 92)},
    137: {"abbr": "SF",  "color": (253, 90, 30)},
    138: {"abbr": "STL", "color": (196, 30, 58)},
    139: {"abbr": "TB",  "color": (9, 44, 92)},
    140: {"abbr": "TEX", "color": (0, 50, 120)},
    141: {"abbr": "TOR", "color": (19, 74, 142)},
    142: {"abbr": "MIN", "color": (0, 43, 92)},
    143: {"abbr": "PHI", "color": (232, 24, 40)},
    144: {"abbr": "ATL", "color": (19, 39, 79)},
    145: {"abbr": "CWS", "color": (39, 37, 31)},
    146: {"abbr": "MIA", "color": (0, 163, 224)},
    147: {"abbr": "NYY", "color": (12, 35, 64)},
    158: {"abbr": "MIL", "color": (18, 40, 75)},
}


class RedSoxApp(MatrixApp):
    """Split-screen MLB scoreboard for the Red Sox with standings fallback"""

    TEAM_ID = 111  # Boston Red Sox
    AL_EAST_DIV_ID = 201

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("RedSox", config)
        self._is_live = False

    def _load_fonts(self):
        """Load fonts with fallback to default."""
        try:
            bold = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
            regular = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
            return {
                'team': ImageFont.truetype(bold, 10),
                'score': ImageFont.truetype(bold, 14),
                'info': ImageFont.truetype(regular, 8),
                'tiny': ImageFont.truetype(regular, 6),
                'standings': ImageFont.truetype(regular, 8),
                'header': ImageFont.truetype(bold, 8),
            }
        except Exception:
            default = ImageFont.load_default()
            return {k: default for k in ('team', 'score', 'info', 'tiny', 'standings', 'header')}

    def _fetch_game(self) -> Optional[dict]:
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
        home = game.get('teams', {}).get('home', {})
        away = game.get('teams', {}).get('away', {})

        home_id = home.get('team', {}).get('id', 0)
        away_id = away.get('team', {}).get('id', 0)
        home_score = home.get('score', 0) or 0
        away_score = away.get('score', 0) or 0

        linescore = game.get('linescore', {})
        inning = linescore.get('currentInning', 0)
        inning_half = linescore.get('inningHalf', '')
        outs = linescore.get('outs', 0) or 0
        offense = linescore.get('offense', {})

        runners = {
            'first': 'first' in offense,
            'second': 'second' in offense,
            'third': 'third' in offense,
        }

        # Game time for scheduled games
        game_time = game.get('gameDate', '')
        try:
            dt = datetime.strptime(game_time, "%Y-%m-%dT%H:%M:%SZ")
            local_hour = (dt.hour - 5) % 24
            ampm = 'PM' if local_hour >= 12 else 'AM'
            display_hour = local_hour % 12 or 12
            display_time = f"{display_hour}:{dt.strftime('%M')}{ampm}"
        except Exception:
            display_time = "TBD"

        return {
            'status': status_code,
            'away_id': away_id,
            'home_id': home_id,
            'away_score': away_score,
            'home_score': home_score,
            'inning': inning,
            'inning_half': inning_half,
            'outs': outs,
            'runners': runners,
            'game_time': display_time,
        }

    def _fetch_standings(self) -> List[dict]:
        """Fetch AL East standings."""
        year = datetime.now().year
        url = (
            f"https://statsapi.mlb.com/api/v1/standings"
            f"?leagueId=103&season={year}&standingsTypes=regularSeason"
        )
        try:
            resp = requests.get(url, timeout=8)
            data = resp.json()
        except Exception as e:
            print(f"RedSox standings error: {e}")
            return []

        for record in data.get('records', []):
            div_id = record.get('division', {}).get('id', 0)
            if div_id == self.AL_EAST_DIV_ID:
                teams = []
                for tr in record.get('teamRecords', []):
                    tid = tr.get('team', {}).get('id', 0)
                    info = TEAMS.get(tid, {"abbr": "???", "color": (128, 128, 128)})
                    gb = tr.get('gamesBack', '-')
                    teams.append({
                        'team_id': tid,
                        'abbr': info['abbr'],
                        'color': info['color'],
                        'wins': tr.get('wins', 0),
                        'losses': tr.get('losses', 0),
                        'gb': gb,
                    })
                return teams
        return []

    def _draw_bases(self, draw, runners: dict, x: int, y: int):
        """Draw base diamond indicators."""
        positions = [
            ((x, y - 5), 'second'),
            ((x - 5, y), 'third'),
            ((x + 5, y), 'first'),
        ]
        for (bx, by), key in positions:
            color = (255, 200, 0) if runners.get(key) else (60, 60, 60)
            draw.polygon([
                (bx, by - 2), (bx + 2, by),
                (bx, by + 2), (bx - 2, by)
            ], fill=color)

    def _draw_outs(self, draw, outs: int, x: int, y: int):
        """Draw out indicators (3 circles)."""
        for i in range(3):
            color = (255, 200, 0) if i < outs else (60, 60, 60)
            cx = x + i * 5
            draw.ellipse([cx, y, cx + 3, y + 3], fill=color)

    def _draw_scoreboard(self, game: dict) -> Image.Image:
        """Draw split-screen scoreboard."""
        fonts = self._load_fonts()
        img = Image.new('RGB', (64, 32), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        away_id = game['away_id']
        home_id = game['home_id']
        away_info = TEAMS.get(away_id, {"abbr": "???", "color": (128, 128, 128)})
        home_info = TEAMS.get(home_id, {"abbr": "???", "color": (128, 128, 128)})

        # Team color bars (left strip, 4px wide)
        draw.rectangle([0, 0, 3, 15], fill=away_info['color'])
        draw.rectangle([0, 16, 3, 31], fill=home_info['color'])

        # Divider line between rows
        draw.line([(0, 15), (63, 15)], fill=(40, 40, 40))

        # Team abbreviations
        draw.text((6, 2), away_info['abbr'], fill=(255, 255, 255), font=fonts['team'])
        draw.text((6, 17), home_info['abbr'], fill=(255, 255, 255), font=fonts['team'])

        status = game['status']

        # Pre-game states: S=Scheduled, P=Pre-Game, PW=Pregame Warmup, PI=Pregame Incomplete
        if status in ('S', 'P', 'PW', 'PI'):
            # Not yet started — show game time instead of score
            draw.text((30, 1), game['game_time'], fill=(200, 200, 200), font=fonts['score'])
        else:
            # Live or Final — show scores
            away_str = str(game['away_score'])
            home_str = str(game['home_score'])
            draw.text((34, 1), away_str, fill=(255, 255, 255), font=fonts['score'])
            draw.text((34, 16), home_str, fill=(255, 255, 255), font=fonts['score'])

            if status == 'I':
                # Bases at top right
                self._draw_bases(draw, game['runners'], 56, 7)

                # Half-inning triangle below divider: green up = top, red down = bottom
                is_top = game['inning_half'].lower().startswith('top')
                if is_top:
                    draw.polygon([(52, 17), (49, 21), (55, 21)], fill=(0, 200, 0))
                else:
                    draw.polygon([(52, 21), (49, 17), (55, 17)], fill=(200, 0, 0))
                draw.text((57, 15), str(game['inning']), fill=(255, 200, 0), font=fonts['tiny'])

                # Outs at bottom right
                self._draw_outs(draw, game['outs'], 49, 27)

            elif status == 'F':
                # Final
                inning = game.get('inning', 9)
                final_str = "F" if inning == 9 else f"F/{inning}"
                draw.text((50, 1), final_str, fill=(255, 200, 0), font=fonts['info'])

        return img

    def _draw_standings(self, standings: List[dict]) -> List[Image.Image]:
        """Draw AL East standings table."""
        fonts = self._load_fonts()
        frames = []

        # All 5 teams fit in two frames if needed, but try one frame first
        # Header + 5 teams at ~6px each = 30px + header, tight but doable
        # Use 2 frames: header+3 teams, then header+2 teams

        if len(standings) <= 3:
            chunks = [standings]
        else:
            chunks = [standings[:3], standings[3:]]

        for chunk_idx, chunk in enumerate(chunks):
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Header
            draw.text((1, 0), "AL EAST", fill=(255, 200, 0), font=fonts['header'])
            draw.text((38, 0), "W", fill=(150, 150, 150), font=fonts['header'])
            draw.text((48, 0), "L", fill=(150, 150, 150), font=fonts['header'])

            # Team rows
            for i, team in enumerate(chunk):
                y = 9 + i * 8
                is_sox = (team['team_id'] == self.TEAM_ID)
                text_color = (200, 20, 20) if is_sox else (200, 200, 200)

                draw.text((1, y), team['abbr'], fill=text_color, font=fonts['standings'])
                draw.text((34, y), str(team['wins']), fill=text_color, font=fonts['standings'])
                draw.text((46, y), str(team['losses']), fill=text_color, font=fonts['standings'])

                # Games back
                gb = team['gb']
                gb_str = "-" if gb == '-' or gb == '0' else str(gb)
                draw.text((56, y), gb_str, fill=text_color, font=fonts['standings'])

            frames.append(img)

        return frames

    def get_frames(self) -> List[Image.Image]:
        game = self._fetch_game()
        if game:
            self._is_live = (game['status'] == 'I')
            img = self._draw_scoreboard(game)
            return [img] * 12
        else:
            self._is_live = False
            standings = self._fetch_standings()
            if standings:
                imgs = self._draw_standings(standings)
                return imgs * 6
            # Fallback
            img = Image.new('RGB', (64, 32), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 10), "No game", fill=(150, 150, 150))
            return [img] * 12

    def needs_refresh(self) -> bool:
        interval = 10 if self._is_live else 600
        return time.time() - self.last_refresh > interval
