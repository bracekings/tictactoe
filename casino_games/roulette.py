"""A minimal roulette game module."""

import pygame
import random


class RouletteGame:
    """Very simple roulette simulator.

    Controls:
        SPACE - spin the wheel
        ESC   - return to casino menu

    The player always bets on "red" for now; future improvements
    could allow selecting number, black, odd/even, etc.
    """

    # wheel numbers paired with their colours
    _wheel = [
        (0, "green"),
        (32, "red"), (15, "black"), (19, "red"), (4, "black"), (21, "red"),
        (2, "black"), (25, "red"), (17, "black"), (34, "red"), (6, "black"),
        (27, "red"), (13, "black"), (36, "red"), (11, "black"), (30, "red"),
        (8, "black"), (23, "red"), (10, "black"), (5, "red"), (24, "black"),
        (16, "red"), (33, "black"), (1, "red"), (20, "black"), (14, "red"),
        (31, "black"), (9, "red"), (22, "black"), (18, "red"), (29, "black"),
        (7, "red"), (28, "black"), (12, "red"), (35, "black"), (3, "red"),
        (26, "black"),
    ]

    def __init__(self, screen_size, player=None):
        self.width, self.height = screen_size
        self.player = player
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.last_spin = None
        self.spinning = False
        # betting state
        self.bet_type = "red"  # default bet
        self.bet_amount = 10
        self.message = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self.spinning:
                # betting/deduction happens in spin()
                self.spin()
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.key == pygame.K_r:
                self.bet_type = "red"
            elif event.key == pygame.K_b:
                self.bet_type = "black"
            elif event.key == pygame.K_g:
                self.bet_type = "green"
            elif event.key == pygame.K_UP:
                self.bet_amount = min(self.bet_amount + 10, self.player.balance if self.player else self.bet_amount + 10)
            elif event.key == pygame.K_DOWN:
                self.bet_amount = max(1, self.bet_amount - 10)

    def update(self):
        # no animation currently
        pass

    def draw(self, surface):
        surface.fill((0, 0, 0))
        title = self.font.render("Roulette", True, (255, 255, 255))
        surface.blit(title, (50, 50))

        # show current bet and player balance
        if self.player:
            bal = self.small_font.render(f"Balance: ${self.player.balance}", True, (255, 255, 0))
            surface.blit(bal, (50, 100))
        betinfo = self.small_font.render(f"Bet: {self.bet_amount} on {self.bet_type}", True, (200, 200, 200))
        surface.blit(betinfo, (50, 130))

        if self.last_spin is not None:
            num, color = self.last_spin
            col = (0, 255, 0) if color == "green" else ((255, 0, 0) if color == "red" else (0, 0, 0))
            result = self.font.render(str(num), True, col)
            surface.blit(result, (self.width // 2 - 50, self.height // 2 - 50))
            detail = self.small_font.render(color.upper(), True, col)
            surface.blit(detail, (self.width // 2 - 50, self.height // 2 + 10))

        instr = self.small_font.render("SPACE=spin, R/B/G choose, UP/DN bet, ESC=menu", True, (200, 200, 200))
        surface.blit(instr, (50, self.height - 40))

        if self.message:
            msgsurf = self.small_font.render(self.message, True, (0, 255, 0) if "Win" in self.message else (255, 0, 0))
            surface.blit(msgsurf, (50, self.height - 70))

    def spin(self):
        self.spinning = True
        self.last_spin = random.choice(self._wheel)
        self.spinning = False
        # settle bet
        if self.player:
            payout = 0
            num, color = self.last_spin
            if self.bet_type == "red" and color == "red":
                payout = self.bet_amount
            elif self.bet_type == "black" and color == "black":
                payout = self.bet_amount
            elif self.bet_type == "green" and color == "green":
                payout = self.bet_amount * 35
            # TODO: number bets later
            self.player.adjust(payout)
            if payout > 0:
                self.message = f"Win ${payout}!"
            else:
                self.message = "Lose"
