import pygame
import random


class BlackjackGame:
    """Simplified blackjack game with betting, hit/stand and dealer play.

    Controls:
        UP/DOWN: adjust wager in betting phase
        ENTER: place bet / continue after round
        H: hit (draw card)
        S: stand
        ESC: back to menu (allowed only between rounds)
    """

    def __init__(self, screen_size, player=None):
        self.width, self.height = screen_size
        self.player = player
        self.font = pygame.font.Font(None, 36)
        self.small = pygame.font.Font(None, 24)

        # state
        self.phase = "betting"  # "betting", "player", "dealer", "result"
        self.bet = 10
        self.min_bet = 1

        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.message = "Place your bet"

    def _build_deck(self):
        ranks = ["A"] + [str(n) for n in range(2, 11)] + ["J", "Q", "K"]
        suits = ["S", "H", "D", "C"]  # Spades, Hearts, Diamonds, Clubs
        self.deck = [r + s for r in ranks for s in suits]
        random.shuffle(self.deck)

    def _draw_card(self):
        if not self.deck:
            self._build_deck()
        return self.deck.pop()

    def _hand_value(self, hand):
        total = 0
        aces = 0
        for card in hand:
            r = card[:-1]
            if r in ("J", "Q", "K"):
                total += 10
            elif r == "A":
                aces += 1
                total += 1
            else:
                total += int(r)
        # upgrade some aces to 11
        for _ in range(aces):
            if total + 10 <= 21:
                total += 10
        return total

    def _start_round(self):
        self._build_deck()
        self.player_hand = [self._draw_card(), self._draw_card()]
        self.dealer_hand = [self._draw_card(), self._draw_card()]
        self.phase = "player"
        self.message = "Hit (H) or Stand (S)?"

    def _end_round(self, result):
        payout = 0
        if result == "win":
            payout = self.bet
        elif result == "blackjack":
            payout = int(self.bet * 1.5)
        elif result == "push":
            payout = 0
        elif result == "lose":
            payout = -self.bet
        if self.player:
            self.player.adjust(payout)
        self.message = f"{result.capitalize()} (balance ${self.player.balance})"
        self.phase = "result"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.phase == "betting":
                if event.key == pygame.K_UP:
                    maxbet = self.player.balance if self.player else self.bet + 1
                    self.bet = min(maxbet, self.bet + 1)
                elif event.key == pygame.K_DOWN:
                    self.bet = max(self.min_bet, self.bet - 1)
                elif event.key == pygame.K_RETURN:
                    self._start_round()
            elif self.phase == "player":
                if event.key == pygame.K_h:
                    self.player_hand.append(self._draw_card())
                    if self._hand_value(self.player_hand) > 21:
                        self._end_round("lose")
                elif event.key == pygame.K_s:
                    self.phase = "dealer"
                    while self._hand_value(self.dealer_hand) < 17:
                        self.dealer_hand.append(self._draw_card())
                    ph = self._hand_value(self.player_hand)
                    dh = self._hand_value(self.dealer_hand)
                    if ph > 21:
                        self._end_round("lose")
                    elif dh > 21 or ph > dh:
                        self._end_round("win")
                    elif ph == dh:
                        self._end_round("push")
                    else:
                        self._end_round("lose")
            elif self.phase == "result":
                if event.key == pygame.K_RETURN:
                    self.phase = "betting"
                    self.message = "Place your bet"
            if event.key == pygame.K_ESCAPE and self.phase != "player":
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _draw_suit_symbol(self, surface, suit, x, y, size=30):
        """Draw a suit symbol (S, H, D, C) at the given position."""
        if suit == "S":  # Spade - inverted triangle with stem
            points = [(x, y - size), (x - size, y), (x + size, y)]
            pygame.draw.polygon(surface, (0, 0, 0), points)
            pygame.draw.line(surface, (0, 0, 0), (x, y), (x, y + size // 2), 2)
        elif suit == "H":  # Heart - two circles on top, point below
            pygame.draw.circle(surface, (255, 0, 0), (x - size // 2, y - size // 3), size // 3)
            pygame.draw.circle(surface, (255, 0, 0), (x + size // 2, y - size // 3), size // 3)
            points = [(x - size, y + size // 3), (x, y + size), (x + size, y + size // 3)]
            pygame.draw.polygon(surface, (255, 0, 0), points)
        elif suit == "D":  # Diamond - rotated square
            points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
            pygame.draw.polygon(surface, (255, 0, 0), points)
        elif suit == "C":  # Club - circle on top, stem below
            pygame.draw.circle(surface, (0, 0, 0), (x, y - size // 3), size // 3)
            pygame.draw.line(surface, (0, 0, 0), (x, y - size // 6), (x, y + size // 2), 2)
            # three lobes
            for offset in [-size // 3, 0, size // 3]:
                pygame.draw.circle(surface, (0, 0, 0), (x + offset, y), size // 4)

    def update(self):
        pass

    def draw(self, surface):
        surface.fill((0, 0, 0))
        if self.player:
            bal = self.font.render(f"Balance: ${self.player.balance}", True, (255, 255, 0))
            surface.blit(bal, (50, 20))
        if self.phase == "betting":
            text = self.font.render(f"Bet: ${self.bet}", True, (255, 255, 255))
            surface.blit(text, (50, self.height // 2 - 20))
            info = self.small.render("Use UP/DOWN to change, ENTER to deal", True, (200,200,200))
            surface.blit(info, (50, self.height // 2 + 30))
        else:
            ph = " ".join(self.player_hand)
            dh = " ".join(self.dealer_hand) if self.phase in ("dealer","result") else self.dealer_hand[0] + " ??"
            pval = self._hand_value(self.player_hand)
            dval = self._hand_value(self.dealer_hand) if self.phase in ("dealer","result") else "?"
            # Draw player hand with suit symbols
            ph_text = self.font.render(f"You: ", True, (255,255,255))
            surface.blit(ph_text, (50, self.height // 2 - 40))
            card_x = 250
            for card in self.player_hand:
                rank = card[:-1]
                suit = card[-1]
                card_surf = pygame.Surface((60, 90))
                card_surf.fill((240, 240, 240))
                pygame.draw.rect(card_surf, (0, 0, 0), (0, 0, 60, 90), 2)
                rank_text = pygame.font.Font(None, 24).render(rank, True, (0, 0, 0))
                card_surf.blit(rank_text, (5, 5))
                self._draw_suit_symbol(card_surf, suit, 30, 45, size=20)
                surface.blit(card_surf, (card_x, self.height // 2 - 40))
                card_x += 70
            pval_text = self.small.render(f"({pval})", True, (255,255,255))
            surface.blit(pval_text, (card_x, self.height // 2 - 40))
            # Draw dealer hand with suit symbols
            dh_text = self.font.render(f"Dealer: ", True, (255,255,255))
            surface.blit(dh_text, (50, self.height // 2 + 10))
            card_x = 280
            dealer_cards = self.dealer_hand if self.phase in ("dealer","result") else [self.dealer_hand[0]]
            for i, card in enumerate(dealer_cards):
                if i == 1 and self.phase not in ("dealer","result"):
                    # Hidden card
                    card_surf = pygame.Surface((60, 90))
                    card_surf.fill((0, 100, 200))
                    pygame.draw.rect(card_surf, (255, 255, 255), (0, 0, 60, 90), 2)
                    pygame.draw.line(card_surf, (255, 255, 255), (0, 45), (60, 45), 1)
                    surface.blit(card_surf, (card_x, self.height // 2 + 10))
                else:
                    rank = card[:-1]
                    suit = card[-1]
                    card_surf = pygame.Surface((60, 90))
                    card_surf.fill((240, 240, 240))
                    pygame.draw.rect(card_surf, (0, 0, 0), (0, 0, 60, 90), 2)
                    rank_text = pygame.font.Font(None, 24).render(rank, True, (0, 0, 0))
                    card_surf.blit(rank_text, (5, 5))
                    self._draw_suit_symbol(card_surf, suit, 30, 45, size=20)
                    surface.blit(card_surf, (card_x, self.height // 2 + 10))
                card_x += 70
            dval_text = self.small.render(f"({dval})", True, (255,255,255))
            surface.blit(dval_text, (card_x, self.height // 2 + 10))
            msg = self.font.render(self.message, True, (255,255,255))
            surface.blit(msg, (50, self.height // 2 + 70))
