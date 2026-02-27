from minesweeper.generator import MinesweeperBoard
from minesweeper.utils import stringify_board, round_prediction, linNorm
from minesweeper.stats import stats
from minesweeper.config import config


class MinesweeperAPI(MinesweeperBoard):
    def __init__(
        self,
        dimension=config.DEFAULT_BOARD_DIMENSION,
        bomb_percentage=config.DEFAULT_BOMB_PERCENTAGE,
        revealed=[],
        radius=config.DEFAULT_AI_RADIUS,
        trainingsdata_amount=config.DEFAULT_TRAININGSDATA_AMOUNT,
        include_bomb_count=config.DEFAULT_INCLUDE_BOMB_COUNT,
        include_hidden_count=config.DEFAULT_INCLUDE_HIDDEN_COUNT,
    ):
        super().__init__(dimension, bomb_percentage, revealed)
        self.set_hidden_board()
        self.moves = 0
        self.radius = radius
        self.trainingsdata_amount = trainingsdata_amount
        self.ai = None
        self.has_died = False
        self.include_bomb_count = include_bomb_count
        self.include_hidden_count = include_hidden_count

    def set_hidden_board(self):
        hidden_board = [[self.HIDDEN] * self.size for _ in range(self.size)]
        self.hidden_board = hidden_board
        return self.hidden_board

    def reveal(self, x, y, is_initial=True):
        if self.moves == 0:
            self.safe_game(x, y)
        if not (0 <= x < self.size and 0 <= y < self.size):
            raise IndexError
        cell = self.number_board[y][x]
        hidden_cell = self.hidden_board[y][x]
        if hidden_cell == self.FLAG:
            return self.hidden_board, False
        elif hidden_cell == cell and is_initial:
            for ny, nx in self.iter_neighborhood(x, y, 1):
                _, died = self.reveal(nx, ny, False)
                if died:
                    return self.hidden_board, True
            return self.hidden_board, False
        elif cell == self.BOMB:
            self.hidden_board = [row[:] for row in self.number_board]
            self.moves += 1
            self.has_died = True
            print("Died ☠")
            return self.number_board, True
        elif cell > 0:
            self.moves += 1
            self.hidden_board[y][x] = self.number_board[y][x]
            return self.hidden_board, False
        elif cell == 0:
            self.moves += 1
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
        if number == self.HIDDEN:
            return "□"
        if number == self.BOMB:
            return "*"
        return str(number)

    def get_cell(self, x, y, board=None):
        if board is None:
            board = self.hidden_board
        return board[y][x]

    def flag(self, x, y):
        cell = self.hidden_board[y][x]
        if cell == self.HIDDEN:
            self.hidden_board[y][x] = self.FLAG
        elif cell == self.FLAG:
            self.hidden_board[y][x] = self.HIDDEN

    def get_hidden_cell_count(self):
        summe = 0
        for row in self.hidden_board:
            for cell in row:
                if cell == self.HIDDEN:
                    summe += 1
        return summe

    def has_won(self, died=False):
        if died:
            return
        has_won = (
            self.get_hidden_cell_count() + self.get_flag_count() - self.bomb_count == 0
        )
        return has_won

    def ended(self):
        has_ended = self.has_died or self.has_won()
        return has_ended

    def __str__(self):
        hidden_board = [
            [self.convert(cell) for cell in row] for row in self.hidden_board
        ]
        return stringify_board(hidden_board)

    def reset(self):
        stats.log(self.has_won(), self.has_died, self.moves, self.bomb_count, self.size)
        self.moves = 0
        self.set_hidden_board()
        self.has_died = False

    def safe_game(self, x, y):
        radius = self.radius
        trainingsdata_amount = self.trainingsdata_amount
        ai = self.ai
        self.__init__(
            self.size, self.bomb_percentage, [(x, y)], radius, trainingsdata_amount
        )
        self.ai = ai

    def predict(self, coordinates):
        if self.ai is None:
            from minesweeper.ai import MinesweeperAI

            self.ai = MinesweeperAI(
                self.radius,
                self.trainingsdata_amount,
                self.bomb_percentage,
                self.include_bomb_count,
                self.include_hidden_count,
            )
        prediction = self.ai.predict(self, coordinates)[:, 1][0]
        if config.CONSIDER_UNKNOWNS:
            return self.weigh_prediction_unknowns(coordinates, prediction)
        else: 
            return prediction
        
    def weigh_prediction_unknowns(self, coordinates, prediction):
            x, y = coordinates
            neighborhood = self.get_out_of_bounds_neighborhood(
                self.hidden_board, x, y, config.NIEGHBORHOOD_RELEVANT
            )
            unknown_count = self.count_elements(neighborhood, self.HIDDEN) + self.count_elements(neighborhood, self.OUT_OF_BOUNDS)
            # Get max possible unknown cells in neighborhood
            max_neighborhood_size = (config.NIEGHBORHOOD_RELEVANT * 2 + 1) ** 2
            # Normalize unknown count to 0-1 range
            norm_unknown_count = linNorm(unknown_count, max_neighborhood_size, 0, 1, 0)
            # Soften the uncertainty effect to avoid collapsing toward 50%
            uncertainty_weight = config.PREDICTION_UNCERTAINTY_WEIGHT
            confidence = 1 - (norm_unknown_count * uncertainty_weight)
            # Pull uncertain predictions toward 50% (maximum uncertainty)
            return (
                prediction * confidence
                + config.PREDICTION_UNCERTAINTY_CENTER * (1 - confidence)
            )

    def predict_all(self):
        predictions = []
        for y, row in enumerate(self.hidden_board):
            current_row = []
            for x, cell in enumerate(row):
                if cell == self.HIDDEN:
                    prediction = self.predict((x, y))
                    current_row.append(round_prediction(prediction))
                else:
                    current_row.append(-1)
            predictions.append(current_row)
        return predictions

    def ai_move(self, flagging=False):
        predictions = self.predict_all()
        smallest = config.PREDICTION_SCALE_MAX
        smallest_coordinates = None
        largest = 0
        largest_coordinates = None
        for y, row in enumerate(predictions):
            for x, cell in enumerate(row):
                if cell < smallest and 0 < cell < config.PREDICTION_SCALE_MAX:
                    smallest = cell
                    smallest_coordinates = (x, y)
                elif cell > largest and 0 < cell < config.PREDICTION_SCALE_MAX:
                    largest = cell
                    largest_coordinates = (x, y)
        if smallest_coordinates is None or largest_coordinates is None:
            return
        if flagging and config.PREDICTION_SCALE_MAX - largest < smallest:
            self.flag(largest_coordinates[0], largest_coordinates[1])
            return largest_coordinates
        else:
            self.reveal(smallest_coordinates[0], smallest_coordinates[1])
            return smallest_coordinates

    def count_elements(self, matrix, element):
        count = 0
        for row in matrix:
            for cell in row:
                if cell == element:
                    count += 1
        return count

    def get_flag_count(self, matrix=None):
        if matrix is None:
            matrix = self.hidden_board
        return self.count_elements(matrix, self.FLAG)

    def get_revealed_count(self, matrix=None):
        if matrix is None:
            matrix = self.hidden_board
        for row in matrix:
            for cell in row:
                if 0 <= cell <= 8:
                    count += 1
        return count


if __name__ == "__main__":
    board = MinesweeperAPI(11, 20, [[1, 2]])
    print(
        stringify_board(
            board.get_out_of_bounds_neighborhood(board.number_board, 0, 0, 1)
        )
    )
    print(stringify_board(board.get_number_board()))
    print(board)
    while True:
        x = int(input("x = "))
        y = int(input("y = "))
        _, died = board.reveal(x, y)
        print(board)
        if died:
            break
