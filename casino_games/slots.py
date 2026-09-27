import pygame
import random


class SlotGame:
    def __init__(self, screen_size, player=None):
        self.width, self.height = screen_size
        self.player = player
        # symbol set and multipliers (use simple letters to avoid font/emoji issues)
        # original emoji equivalents: 🍒, 🍋, 7, BAR, 🍉, 🍇
        self.symbols = ["C", "L", "7", "BAR", "W", "G"]
        # C=cherry, L=lemon, 7=seven, BAR, W=watermelon, G=grapes
        self.mult = {"C": 2, "L": 3, "7": 5, "BAR": 10, "W": 20, "G": 50}
        # reels: each column has copy of symbols
        self.reels = [self.symbols[:] for _ in range(3)]
        # current 3x3 grid (columns x rows) - initialize with random symbols
        self.current = [[random.choice(self.reels[c]) for _ in range(3)] for c in range(3)]
        self.font = pygame.font.Font(None, 72)
        self.spinning = False
        self.spin_start = 0
        self.spin_duration = 700  # milliseconds per spin animation
        # betting state
        self.bet_amount = 10
        self.bet_step = 10
        self.min_bet = 1
        # flow spin options and counters
        self.flows = [("Basic", 1), ("Pro", 2), ("Mega", 5), ("Ultra", 10)]
        self.flow_index = 0
        self.num_spins = 1
        self.remaining_spins = 0
        # jackpot pool
        self.jackpot = 1000
        self.message = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self.spinning:
                self.start_sequence()
            elif event.key == pygame.K_UP and not self.spinning:
                # adjust bet up
                maxbet = self.player.balance if self.player else self.bet_amount + self.bet_step
                self.bet_amount = min(maxbet, self.bet_amount + self.bet_step)
            elif event.key == pygame.K_DOWN and not self.spinning:
                self.bet_amount = max(self.min_bet, self.bet_amount - self.bet_step)
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif not self.spinning and event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                self.flow_index = event.key - pygame.K_1
            elif not self.spinning and event.key in (pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                self.num_spins = event.key - pygame.K_4

    def update(self):
        if self.spinning:
            now = pygame.time.get_ticks()
            if now - self.spin_start >= self.spin_duration:
                # finish this spin and possibly queue next
                self.finish_spin()
                if self.remaining_spins > 0:
                    self.start_spin()
                else:
                    self.spinning = False
            else:
                # animation: fill grid with random symbols
                for c in range(3):
                    for r in range(3):
                        self.current[c][r] = random.choice(self.reels[c])

    def _draw_symbol(self, surface, symbol, x, y, size=60):
        """Draw a visual symbol at the given position."""
        if symbol == "C":  # Cherry - two red circles
            pygame.draw.circle(surface, (200, 0, 0), (x - 15, y - 10), size // 3)
            pygame.draw.circle(surface, (200, 0, 0), (x + 15, y - 10), size // 3)
            pygame.draw.line(surface, (100, 50, 0), (x, y - 10), (x, y + 10), 2)  # stem
        elif symbol == "L":  # Lemon - yellow circle
            pygame.draw.circle(surface, (255, 220, 0), (x, y), size // 2)
            pygame.draw.circle(surface, (200, 180, 0), (x, y), size // 2, 2)  # outline
        elif symbol == "7":  # Seven - stylized number
            pygame.draw.line(surface, (200, 200, 0), (x - 20, y - 30), (x + 20, y - 30), 4)  # top
            pygame.draw.line(surface, (200, 200, 0), (x + 20, y - 30), (x - 20, y + 30), 4)  # diagonal
        elif symbol == "BAR":  # BAR - three horizontal rectangles
            for i in range(3):
                pygame.draw.rect(surface, (255, 100, 0), (x - 20, y - 20 + i * 20, 40, 12))
        elif symbol == "W":  # Watermelon - green circle with red inside
            pygame.draw.circle(surface, (0, 150, 0), (x, y), size // 2)  # outer green
            pygame.draw.circle(surface, (200, 0, 0), (x, y), size // 3)  # inner red
            for angle in [0, 90, 180, 270]:
                seed_x = x + (size // 3 - 5) * pygame.math.cos(angle * 3.14159 / 180)
                seed_y = y + (size // 3 - 5) * pygame.math.sin(angle * 3.14159 / 180)
                pygame.draw.circle(surface, (0, 0, 0), (int(seed_x), int(seed_y)), 2)
        elif symbol == "G":  # Grapes - cluster of purple circles
            for dx in [-15, 0, 15]:
                for dy in [-10, 5]:
                    pygame.draw.circle(surface, (150, 50, 150), (x + dx, y + dy), size // 4)

    def draw(self, surface):
        surface.fill((0, 0, 0))
        # draw 3x3 grid on left side (reserve right area for legend)
        grid_start_x = 100
        grid_start_y = self.height // 2 - 36
        for c in range(3):
            for r in range(3):
                sym = self.current[c][r]
                if sym is not None:
                    x = grid_start_x + c * 150 + 75
                    y = grid_start_y + r * 80 + 40
                    self._draw_symbol(surface, sym, x, y, size=60)

        # display balance and current bet
        if self.player:
            bal_surf = self.font.render(f"${self.player.balance}", True, (255, 255, 0))
            surface.blit(bal_surf, (50, 50))
        bet_surf = pygame.font.Font(None, 36).render(f"Bet: ${self.bet_amount}", True, (200, 200, 200))
        surface.blit(bet_surf, (50, 100))
        # show flow/number of spins
        flowname, mult = self.flows[self.flow_index]
        mode_surf = pygame.font.Font(None, 24).render(f"Mode: {flowname} x{mult}", True, (200, 200, 200))
        surface.blit(mode_surf, (50, 130))
        spins_surf = pygame.font.Font(None, 24).render(f"Spins: {self.num_spins}", True, (200, 200, 200))
        surface.blit(spins_surf, (50, 150))
        # legend for symbols (draw on right side)
        legend_x = self.width - 250
        yoff = 200
        for sym, m in self.mult.items():
            leg = pygame.font.Font(None, 24).render(f"{sym}: x{m}", True, (255, 255, 255))
            surface.blit(leg, (legend_x, yoff))
            yoff += 30
        jp = pygame.font.Font(None, 24).render(f"Jackpot: ${self.jackpot}", True, (255, 0, 0))
        surface.blit(jp, (legend_x, yoff + 20))

        instr = pygame.font.Font(None, 24).render("UP/DOWN bet, 1-4 flow, 5-9 spins, SPACE spin, ESC menu", True, (200,200,200))
        surface.blit(instr, (50, self.height - 40))

        if self.message:
            msgsurf = pygame.font.Font(None, 36).render(self.message, True, (0, 255, 0) if "Win" in self.message else (255, 0, 0))
            surface.blit(msgsurf, (50, self.height - 80))

    def start_sequence(self):
        """Begin a sequence of spins based on current selection."""
        self.remaining_spins = self.num_spins
        self.start_spin()

    def start_spin(self):
        # setup single spin
        self.spinning = True
        self.spin_start = pygame.time.get_ticks()
        flowmult = self.flows[self.flow_index][1]
        self.current_bet = self.bet_amount * flowmult
        if self.player:
            self.player.adjust(-self.current_bet)
        self.jackpot += int(self.current_bet * 0.05)
        self.remaining_spins -= 1
        self.message = ""

    def finish_spin(self):
        # finalize grid
        for c in range(3):
            for r in range(3):
                self.current[c][r] = random.choice(self.reels[c])
        # check rows for wins
        payout = 0
        for r in range(3):
            row = [self.current[c][r] for c in range(3)]
            if row[0] == row[1] == row[2]:
                sym = row[0]
                payout += self.mult.get(sym, 0) * self.current_bet
                if sym == "7":
                    payout += self.jackpot
                    self.jackpot = 1000
        if self.player:
            self.player.adjust(payout)
        self.message = f"Win ${payout}!" if payout > 0 else "Lose"
