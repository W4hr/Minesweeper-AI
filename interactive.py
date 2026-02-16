from trainingsdata import MinesweeperBoard

class MinesweeperAPI(MinesweeperBoard):
    HIDDEN = -1

    def __init__(self, dimension, revealed = []):
        super().__init__(dimension, revealed=revealed)
        self.set_hidden_board()

    def set_hidden_board(self):
        hidden_board = [[self.HIDDEN] * self.size for _ in range(self.size)]
        self.hidden_board = hidden_board
        return self.hidden_board

    def reveal(self, x, y):
        if not (0 <= x < self.size and 0 <= y < self.size):
            raise IndexError
        cell = self.number_board[y][x]
        if cell == self.BOMB:
            self.hidden_board = [row[:] for row in self.number_board]
            print("Died ☠")
            return self.number_board, True
        elif cell > 0:
            self.hidden_board[y][x] = self.number_board[y][x]
            return self.hidden_board, False
        elif cell == 0:
            self.revealZero(x, y)
            return self.hidden_board, False
            
    def revealZero(self, x, y):
        if self.hidden_board[y][x] != self.HIDDEN:
            return
        cell = self.number_board[y][x]
        self.hidden_board[y][x] = cell
        if cell == 0:
            for ny, nx in self.iter_neighborhood(x, y):
                if nx == x and ny == y:
                    continue
                self.revealZero(nx, ny)

    def convert(self, number: int):
        if number == self.HIDDEN: return "□"
        if number == self.BOMB: return "*"
        return str(number)
    
    def get_cell(self, x,y, board = None):
        if board is None:
            board = self.hidden_board
        return board[y][x]

    def __str__(self):
        hidden_board = [[self.convert(cell) for cell in row] for row in self.hidden_board]
        return self.stringify_board(hidden_board)

if __name__ == "__main__":
    board = MinesweeperAPI(10)
    print(board.stringify_board(board.get_number_board()))
    print(board)
    while True:
        x = int(input("x = "))
        y = int(input("y = "))
        _, died = board.reveal(x,y)
        print(board)
        if died: break