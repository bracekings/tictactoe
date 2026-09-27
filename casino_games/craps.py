import pygame
import random


class CrapsGame:
    """Very minimal pass-line only craps.

    Controls:
        SPACE - roll dice
        ESC   - return to menu (only between rounds)

    Rule summary (simplified):
    - On come-out roll (phase 'comeout'):
      7 or 11 = win, 2/3/12 = lose, any other = establishes point and moves to 'point' phase.
    - On point phase, roll until 7 (lose) or point number (win).
    """

    def __init__(self, screen_size, player=None):
        self.width, self.height = screen_size
        self.player = player
        self.font = pygame.font.Font(None, 36)
        self.phase = "comeout"
        self.point = None
        self.message = "Press SPACE to roll"
        self.bet = 10
        self.min_bet = 1

    def _roll(self):
        return random.randint(1, 6) + random.randint(1, 6)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.do_roll()
            elif event.key == pygame.K_ESCAPE and self.phase != "rolling":
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def do_roll(self):
        roll = self._roll()
        if self.phase == "comeout":
            if roll in (7, 11):
                self.win(roll)
            elif roll in (2, 3, 12):
                self.lose(roll)
            else:
                self.point = roll
                self.phase = "point"
                self.message = f"Point established: {roll}. Roll again."
        elif self.phase == "point":
            if roll == self.point:
                self.win(roll)
            elif roll == 7:
                self.lose(roll)
            else:
                self.message = f"Rolled {roll}. Keep rolling."

    def win(self, roll):
        amt = self.bet
        if self.player:
            self.player.adjust(amt)
        self.message = f"Rolled {roll}: You win!"
        self.reset()

    def lose(self, roll):
        amt = -self.bet
        if self.player:
            self.player.adjust(amt)
        self.message = f"Rolled {roll}: You lose."
        self.reset()

    def reset(self):
        self.phase = "comeout"
        self.point = None

    def update(self):
        pass

    def draw(self, surface):
        surface.fill((0, 0, 0))
        if self.player:
            bal = self.font.render(f"Balance: ${self.player.balance}", True, (255, 255, 0))
            surface.blit(bal, (50, 20))
        comp = self.font.render(self.message, True, (255, 255, 255))
        surface.blit(comp, (50, self.height // 2))
