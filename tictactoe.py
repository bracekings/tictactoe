class TicTacToe:
    def __init__(self):
        self.board = [" " for _ in range(9)]
        self.current_player = "X"
    
    def make_move(self, position):
        if self.board[position] == " ":
            self.board[position] = self.current_player
            self.current_player = "O" if self.current_player == "X" else "X"
            return True
        return False
    
    def check_winner(self):
        # Check rows
        for i in range(0, 9, 3):
            if self.board[i] == self.board[i+1] == self.board[i+2] != " ":
                return self.board[i]
        
        # Check columns
        for i in range(3):
            if self.board[i] == self.board[i+3] == self.board[i+6] != " ":
                return self.board[i]
        
        # Check diagonals
        if self.board[0] == self.board[4] == self.board[8] != " ":
            return self.board[0]
        if self.board[2] == self.board[4] == self.board[6] != " ":
            return self.board[2]
        
        # Check for draw
        if " " not in self.board:
            return "Draw"
        
        return None
    
    def display_board(self):
        for i in range(0, 9, 3):
            print(f" {self.board[i]} | {self.board[i+1]} | {self.board[i+2]} ")
            if i < 6:
                print("-----------")

def main():
    game = TicTacToe()
    print("Welcome to Tic Tac Toe!")
    print("Positions are numbered from 0-8, left to right, top to bottom")
    
    while True:
        game.display_board()
        print(f"\nPlayer {game.current_player}'s turn")
        
        try:
            position = int(input("Enter position (0-8): "))
            if position < 0 or position > 8:
                print("Position must be between 0 and 8")
                continue
                
            if not game.make_move(position):
                print("That position is already taken!")
                continue
                
            winner = game.check_winner()
            if winner:
                game.display_board()
                if winner == "Draw":
                    print("\nGame Over! It's a draw!")
                else:
                    print(f"\nGame Over! Player {winner} wins!")
                break
                
        except ValueError:
            print("Please enter a valid number!")

if __name__ == "__main__":
    main()
