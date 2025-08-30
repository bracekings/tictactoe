import tkinter as tk
from tkinter import messagebox
import random

class TicTacToeGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Tic Tac Toe")
        
        # Game state
        self.current_player = "X"
        self.board = [" " for _ in range(9)]
        self.buttons = []
        self.ai_enabled = False
        self.ai_player = "O"
        
        # Mode selection frame
        mode_frame = tk.Frame(self.window)
        mode_frame.grid(row=0, column=0, columnspan=3, pady=10)
        
        tk.Label(mode_frame, text="Game Mode:", font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="2P")
        tk.Radiobutton(mode_frame, text="2 Players", variable=self.mode_var, value="2P", 
                      command=self.change_mode).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="vs AI", variable=self.mode_var, value="AI", 
                      command=self.change_mode).pack(side=tk.LEFT, padx=5)
        
        # Create game board
        board_frame = tk.Frame(self.window)
        board_frame.grid(row=1, column=0, columnspan=3)
        
        for i in range(3):
            for j in range(3):
                button = tk.Button(
                    board_frame,
                    text="",
                    font=('Arial', 20, 'bold'),
                    width=6,
                    height=3,
                    command=lambda row=i, col=j: self.button_click(row, col)
                )
                button.grid(row=i, column=j)
                self.buttons.append(button)
        
        # Create reset button
        reset_button = tk.Button(
            self.window,
            text="Reset Game",
            font=('Arial', 12),
            command=self.reset_game
        )
        reset_button.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Create turn label
        self.turn_label = tk.Label(
            self.window,
            text=f"Player {self.current_player}'s turn",
            font=('Arial', 12)
        )
        self.turn_label.grid(row=4, column=0, columnspan=3)

    def button_click(self, row, col):
        index = row * 3 + col
        if self.board[index] == " ":
            # Human move
            self.board[index] = self.current_player
            self.buttons[index].config(text=self.current_player)
            
            if self.check_winner():
                messagebox.showinfo("Game Over", f"Player {self.current_player} wins!")
                self.reset_game()
                return
            elif " " not in self.board:
                messagebox.showinfo("Game Over", "It's a draw!")
                self.reset_game()
                return
                
            self.current_player = "O" if self.current_player == "X" else "X"
            self.turn_label.config(text=f"Player {self.current_player}'s turn")
            
            # AI move
            if self.ai_enabled and self.current_player == self.ai_player:
                self.window.after(500, self.make_ai_move)  # Small delay for better UX

    def make_ai_move(self):
        if " " not in self.board or self.check_winner():
            return
            
        best_score = float('-inf')
        best_move = None
        
        for i in range(9):
            if self.board[i] == " ":
                self.board[i] = self.ai_player
                score = self.minimax(self.board, 0, False)
                self.board[i] = " "
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        if best_move is not None:
            self.board[best_move] = self.ai_player
            self.buttons[best_move].config(text=self.ai_player)
            
            if self.check_winner():
                messagebox.showinfo("Game Over", "AI wins!")
                self.reset_game()
            elif " " not in self.board:
                messagebox.showinfo("Game Over", "It's a draw!")
                self.reset_game()
            else:
                self.current_player = "X"
                self.turn_label.config(text="Your turn")
                
    def minimax(self, board, depth, is_maximizing):
        if self.check_winner_board(board, self.ai_player):
            return 1
        elif self.check_winner_board(board, "X"):
            return -1
        elif " " not in board:
            return 0
            
        if is_maximizing:
            best_score = float('-inf')
            for i in range(9):
                if board[i] == " ":
                    board[i] = self.ai_player
                    score = self.minimax(board, depth + 1, False)
                    board[i] = " "
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == " ":
                    board[i] = "X"
                    score = self.minimax(board, depth + 1, True)
                    board[i] = " "
                    best_score = min(score, best_score)
            return best_score
            
    def check_winner_board(self, board, player):
        # Check rows
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] == player:
                return True
        
        # Check columns
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] == player:
                return True
        
        # Check diagonals
        if board[0] == board[4] == board[8] == player:
            return True
        if board[2] == board[4] == board[6] == player:
            return True
        
        return False
        
    def change_mode(self):
        self.ai_enabled = (self.mode_var.get() == "AI")
        self.reset_game()

    def check_winner(self):
        # Check rows
        for i in range(0, 9, 3):
            if self.board[i] == self.board[i+1] == self.board[i+2] != " ":
                return True
        
        # Check columns
        for i in range(3):
            if self.board[i] == self.board[i+3] == self.board[i+6] != " ":
                return True
        
        # Check diagonals
        if self.board[0] == self.board[4] == self.board[8] != " ":
            return True
        if self.board[2] == self.board[4] == self.board[6] != " ":
            return True
        
        return False

    def reset_game(self):
        self.board = [" " for _ in range(9)]
        self.current_player = "X"
        for button in self.buttons:
            button.config(text="")
        self.turn_label.config(text=f"Player {self.current_player}'s turn")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    game = TicTacToeGUI()
    game.run()
