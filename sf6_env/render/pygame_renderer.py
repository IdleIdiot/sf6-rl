from __future__ import annotations
from typing import Optional, TYPE_CHECKING

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

if TYPE_CHECKING:
    from sf6_env.engine.game import Game

WIDTH = 800
HEIGHT = 450
GROUND_SCREEN_Y = 380
SCALE_X = WIDTH / 1000.0
SCALE_Y = 1.0

COLOR_BG = (30, 30, 40)
COLOR_P1 = (60, 120, 220)
COLOR_P2 = (220, 60, 60)
COLOR_HITBOX = (220, 50, 50, 160)
COLOR_HURTBOX = (50, 220, 50, 160)
COLOR_HEALTH_BG = (80, 20, 20)
COLOR_HEALTH_FG = (50, 200, 50)
COLOR_DRIVE_BG = (20, 20, 80)
COLOR_DRIVE_FG = (50, 150, 220)
COLOR_BURNOUT = (220, 100, 20)
COLOR_SUPER_FG = (220, 200, 50)
COLOR_TEXT = (240, 240, 240)
COLOR_PROJ = (255, 200, 50)


def world_to_screen(x: float, y: float):
    sx = int(x * SCALE_X)
    sy = int(GROUND_SCREEN_Y - y)
    return sx, sy


class PygameRenderer:
    def __init__(self, headless: bool = False):
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for rendering")
        if not headless:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("SF6 Sim")
        else:
            pygame.init()
            self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)
        self.big_font = pygame.font.SysFont("monospace", 22, bold=True)
        self.headless = headless

    def render(self, game: "Game") -> Optional[object]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None

        self.screen.fill(COLOR_BG)
        pygame.draw.line(self.screen, (80, 80, 80), (0, GROUND_SCREEN_Y), (WIDTH, GROUND_SCREEN_Y), 2)

        self._draw_character(game.p1, COLOR_P1)
        self._draw_character(game.p2, COLOR_P2)
        self._draw_projectiles(game.p1.projectiles)
        self._draw_projectiles(game.p2.projectiles)
        self._draw_hud(game)

        if not self.headless:
            pygame.display.flip()
            self.clock.tick(60)
        return pygame.surfarray.array3d(self.screen)

    def _draw_character(self, char, color) -> None:
        sx, sy = world_to_screen(char.body.x, char.body.y)
        char_w, char_h = 40, 120
        rect = pygame.Rect(sx - char_w // 2, sy - char_h, char_w, char_h)
        pygame.draw.rect(self.screen, color, rect)

        hurtboxes = char.current_hurtboxes()
        for hb in hurtboxes:
            ox = hb["x_offset"] * char.facing
            oy = hb["y_offset"]
            hw = int(hb["w"] * SCALE_X)
            hh = int(hb["h"])
            hx = int((char.body.x + ox) * SCALE_X) - hw // 2
            hy = int(GROUND_SCREEN_Y - char.body.y - oy) - hh
            surf = pygame.Surface((max(1, hw), max(1, hh)), pygame.SRCALPHA)
            surf.fill((50, 220, 50, 80))
            self.screen.blit(surf, (hx, hy))
            pygame.draw.rect(self.screen, (50, 220, 50), (hx, hy, max(1, hw), max(1, hh)), 1)

        move = char.current_move_data
        if move:
            startup = move.get("startup", 1)
            active = move.get("active", 1)
            frame = char.action_frame
            if startup <= frame < startup + active:
                for hb in move.get("hitboxes", []):
                    ox = hb["x_offset"] * char.facing
                    oy = hb["y_offset"]
                    hw = int(hb["w"] * SCALE_X)
                    hh = int(hb["h"])
                    hx = int((char.body.x + ox) * SCALE_X) - hw // 2
                    hy = int(GROUND_SCREEN_Y - char.body.y - oy) - hh
                    surf = pygame.Surface((max(1, hw), max(1, hh)), pygame.SRCALPHA)
                    surf.fill((220, 50, 50, 120))
                    self.screen.blit(surf, (hx, hy))
                    pygame.draw.rect(self.screen, (220, 50, 50), (hx, hy, max(1, hw), max(1, hh)), 2)

        label = self.font.render(char.current_action[:12], True, COLOR_TEXT)
        self.screen.blit(label, (sx - 30, sy - char_h - 18))

    def _draw_projectiles(self, projectiles) -> None:
        for proj in projectiles:
            sx = int(proj.x * SCALE_X)
            sy = int(GROUND_SCREEN_Y - proj.y)
            pw, ph = int(proj.w), int(proj.h)
            pygame.draw.rect(self.screen, COLOR_PROJ, (sx - pw // 2, sy - ph, pw, ph))

    def _draw_hud(self, game: "Game") -> None:
        bar_w = 300
        bar_h = 20
        margin = 20

        p1_hp_pct = game.p1.health / 10000.0
        p2_hp_pct = game.p2.health / 10000.0
        pygame.draw.rect(self.screen, COLOR_HEALTH_BG, (margin, margin, bar_w, bar_h))
        pygame.draw.rect(self.screen, COLOR_HEALTH_FG, (margin, margin, int(bar_w * p1_hp_pct), bar_h))
        pygame.draw.rect(self.screen, COLOR_HEALTH_BG, (WIDTH - margin - bar_w, margin, bar_w, bar_h))
        p2_fill = int(bar_w * p2_hp_pct)
        pygame.draw.rect(self.screen, COLOR_HEALTH_FG, (WIDTH - margin - p2_fill, margin, p2_fill, bar_h))

        drive_bar_h = 10
        drive_y = margin + bar_h + 4
        p1_drive_pct = game.p1.drive.value / 6.0
        p2_drive_pct = game.p2.drive.value / 6.0
        p1_drive_color = COLOR_BURNOUT if game.p1.drive.burnout else COLOR_DRIVE_FG
        p2_drive_color = COLOR_BURNOUT if game.p2.drive.burnout else COLOR_DRIVE_FG
        pygame.draw.rect(self.screen, COLOR_DRIVE_BG, (margin, drive_y, bar_w, drive_bar_h))
        pygame.draw.rect(self.screen, p1_drive_color, (margin, drive_y, int(bar_w * p1_drive_pct), drive_bar_h))
        pygame.draw.rect(self.screen, COLOR_DRIVE_BG, (WIDTH - margin - bar_w, drive_y, bar_w, drive_bar_h))
        p2_drive_fill = int(bar_w * p2_drive_pct)
        pygame.draw.rect(self.screen, p2_drive_color, (WIDTH - margin - p2_drive_fill, drive_y, p2_drive_fill, drive_bar_h))

        super_y = drive_y + drive_bar_h + 4
        for i in range(3):
            filled = game.p1.super_gauge >= (i + 1)
            color = COLOR_SUPER_FG if filled else (60, 60, 20)
            pygame.draw.rect(self.screen, color, (margin + i * 34, super_y, 30, 8))
        for i in range(3):
            filled = game.p2.super_gauge >= (i + 1)
            color = COLOR_SUPER_FG if filled else (60, 60, 20)
            pygame.draw.rect(self.screen, color, (WIDTH - margin - (i + 1) * 34, super_y, 30, 8))

        timer_secs = max(0, (5400 - game.frame_count) // 60)
        timer_text = self.big_font.render(str(timer_secs), True, COLOR_TEXT)
        self.screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, margin))

    def close(self) -> None:
        pygame.quit()
