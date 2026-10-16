#!/usr/bin/env python3
"""Topaz Trove — full-colour Python 3 neon minesweeper arcade for ElbowOS.
https://x.com/ElbowOS
"""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/TOPAZ_TROVE_ElbowOS.mp4")
TITLE, HANDLE = "TOPAZ TROVE", "x.com/ElbowOS"

# Palette — warm golds / deep navy / magenta accents
VOID = (6, 4, 18)
INK = (14, 10, 36)
GOLD = (255, 196, 48)
AMBER = (255, 140, 32)
MAG = (255, 64, 180)
CYAN = (48, 220, 255)
LIME = (120, 255, 80)
WHITE = (248, 244, 255)
ROSE = (255, 80, 110)
NAVY = (8, 16, 48)

COLS, ROWS = 8, 12
CELL = 108
GRID_X = (W - COLS * CELL) // 2
GRID_Y = 280
MINES = 14

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("dejavusans", 72, bold=True)
        self.font_md = pygame.font.SysFont("dejavusans", 48, bold=True)
        self.font_sm = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.font_num = pygame.font.SysFont("dejavusans", 42, bold=True)
        self.reset()

    def reset(self):
        self.grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.revealed = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.alive = True
        self.flash = 0
        self.particles = []
        self.tick = 0
        cells = [(r, c) for r in range(ROWS) for c in range(COLS)]
        random.shuffle(cells)
        for r, c in cells[:MINES]:
            self.grid[r][c] = -1
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == -1:
                    continue
                n = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < ROWS and 0 <= cc < COLS and self.grid[rr][cc] == -1:
                            n += 1
                self.grid[r][c] = n

    def reveal(self, r, c):
        if not (0 <= r < ROWS and 0 <= c < COLS) or self.revealed[r][c]:
            return
        self.revealed[r][c] = True
        val = self.grid[r][c]
        if val == -1:
            self.alive = False
            self.flash = 18
            self.score = max(0, self.score - 40)
            cx = GRID_X + c * CELL + CELL // 2
            cy = GRID_Y + r * CELL + CELL // 2
            for _ in range(18):
                ang = random.uniform(0, math.tau)
                sp = random.uniform(2, 7)
                self.particles.append([cx, cy, math.cos(ang) * sp, math.sin(ang) * sp, random.randint(12, 28), ROSE])
            return
        self.score += 12
        cx = GRID_X + c * CELL + CELL // 2
        cy = GRID_Y + r * CELL + CELL // 2
        for _ in range(6):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(1, 3)
            self.particles.append([cx, cy, math.cos(ang) * sp, math.sin(ang) * sp, random.randint(8, 16), GOLD if val == 0 else CYAN])
        if val == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        self.reveal(r + dr, c + dc)

    def auto_step(self):
        if not self.alive:
            if self.flash <= 0:
                self.reset()
            return
        if self.tick % 8 == 0:
            candidates = [(r, c) for r in range(ROWS) for c in range(COLS) if not self.revealed[r][c]]
            if candidates:
                r, c = random.choice(candidates)
                self.reveal(r, c)
            else:
                self.reset()

    def update_particles(self):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self.particles.remove(p)
        if self.flash > 0:
            self.flash -= 1

    def draw(self, surf):
        surf.fill(VOID)
        for i in range(8):
            pygame.draw.circle(surf, (20 + i * 4, 12 + i * 2, 40), (W // 2, H // 2), 900 - i * 90, 2)
        for r in range(ROWS):
            for c in range(COLS):
                x = GRID_X + c * CELL
                y = GRID_Y + r * CELL
                rect = pygame.Rect(x + 4, y + 4, CELL - 8, CELL - 8)
                if self.revealed[r][c]:
                    if self.grid[r][c] == -1:
                        pygame.draw.rect(surf, ROSE, rect, border_radius=12)
                        pygame.draw.circle(surf, WHITE, rect.center, 18)
                    else:
                        pygame.draw.rect(surf, INK, rect, border_radius=12)
                        pygame.draw.rect(surf, GOLD, rect, 3, border_radius=12)
                        n = self.grid[r][c]
                        if n > 0:
                            cols = [CYAN, LIME, GOLD, AMBER, MAG, ROSE, WHITE, CYAN]
                            col = cols[min(n - 1, 7)]
                            lab = self.font_num.render(str(n), True, col)
                            surf.blit(lab, lab.get_rect(center=rect.center))
                else:
                    pygame.draw.rect(surf, (28, 22, 60), rect, border_radius=12)
                    pygame.draw.rect(surf, MAG, rect, 3, border_radius=12)
                    pygame.draw.circle(surf, (80, 50, 120), (x + 28, y + 28), 8)
        for p in self.particles:
            pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), max(2, p[4] // 3))
        if self.flash > 0:
            alpha = self.flash * 12
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((255, 40, 80, min(180, alpha)))
            surf.blit(flash, (0, 0))
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 140)))
        sc = self.font_md.render(f"SCORE  {self.score}", True, AMBER)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 220)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        surf.blit(handle, handle.get_rect(center=(W // 2, H - 120)))
        status = "BOOM!" if not self.alive else "CLEARING..."
        st = self.font_sm.render(status, True, ROSE if not self.alive else LIME)
        surf.blit(st, st.get_rect(center=(W // 2, 210)))

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        for i in range(frames):
            self.tick += 1
            self.auto_step()
            self.update_particles()
            self.draw(self.screen)
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
            if i % 30 == 0:
                print(f"frame {i}/{frames} score={self.score}")
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and self.alive:
                    mx, my = ev.pos
                    c = (mx - GRID_X) // CELL
                    r = (my - GRID_Y) // CELL
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        self.reveal(r, c)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            self.update_particles()
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
