"""Entry point for the casino application.

This module launches a Pygame window with a simple main menu
from which the player can choose among various casino games.
Each game lives in its own module and exposes a standardized
interface (``handle_event``, ``update``, ``draw``) so that the
main loop can swap between them easily.

At the moment the only built-in game is a placeholder; we'll add
real casino titles such as slots, blackjack, roulette, etc.
"""

import pygame

# we'll lazily import subgames when the player selects them


class GameState:
	MENU = "menu"
	GAME = "game"


class Player:
	"""Simple player state tracker; currently only bankroll."""

	def __init__(self, balance: int = 1000):
		self.balance = balance

	def adjust(self, amount: int) -> None:
		"""Add (or subtract) money from the balance."""

		self.balance += amount


class CasinoApp:
	def __init__(self, width=800, height=600):
		pygame.init()
		self.screen = pygame.display.set_mode((width, height))
		pygame.display.set_caption("Python Casino")
		self.clock = pygame.time.Clock()

		# player data shared across games
		self.player = Player()

		# menu entries map to (display text, factory function)
		self.menu_items = [
			("Slots", self.load_slots),
			("Blackjack", self.load_blackjack),
			("Roulette", self.load_roulette),
			("Craps", self.load_craps),
			("Quit", None),
		]
		self.selected_index = 0
		self.state = GameState.MENU
		self.current_game = None
		self.font = pygame.font.Font(None, 36)

	# placeholder loaders; real ones will import the game modules
	def load_slots(self):
		from casino_games import slots
		# slots may in future modify the bankroll
		return slots.SlotGame(self.screen.get_size(), player=self.player)

	def load_blackjack(self):
		from casino_games import blackjack
		return blackjack.BlackjackGame(self.screen.get_size(), player=self.player)

	def load_roulette(self):
		from casino_games import roulette
		return roulette.RouletteGame(self.screen.get_size(), player=self.player)
	def load_craps(self):
		from casino_games import craps
		return craps.CrapsGame(self.screen.get_size(), player=self.player)

	def run(self):
		running = True
		while running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif self.state == GameState.MENU:
					self.handle_menu_event(event)
				elif self.current_game:
					self.current_game.handle_event(event)

			if self.state == GameState.MENU:
				self.draw_menu()
			elif self.current_game:
				self.current_game.update()
				self.current_game.draw(self.screen)

			pygame.display.flip()
			self.clock.tick(60)

		pygame.quit()

	def handle_menu_event(self, event):
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_UP:
				self.selected_index = (self.selected_index - 1) % len(self.menu_items)
			elif event.key == pygame.K_DOWN:
				self.selected_index = (self.selected_index + 1) % len(self.menu_items)
			elif event.key == pygame.K_RETURN:
				text, loader = self.menu_items[self.selected_index]
				if loader is None:
					# quit entry
					pygame.event.post(pygame.event.Event(pygame.QUIT))
				else:
					self.current_game = loader()
					self.state = GameState.GAME

	def draw_menu(self):
		self.screen.fill((0, 0, 0))
		# display balance at top
		bal_surf = self.font.render(f"Balance: ${self.player.balance}", True, (255, 255, 0))
		self.screen.blit(bal_surf, (100, 20))

		for idx, (text, _) in enumerate(self.menu_items):
			color = (255, 0, 0) if idx == self.selected_index else (255, 255, 255)
			surf = self.font.render(text, True, color)
			self.screen.blit(surf, (100, 100 + idx * 50))


if __name__ == "__main__":
	app = CasinoApp()
	app.run()
