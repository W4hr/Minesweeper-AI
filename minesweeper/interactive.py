from minesweeper.generator import MinesweeperBoard
from minesweeper.utils import stringify_board, round_prediction, linNorm
from minesweeper.stats import stats
from minesweeper.config import config
from global_config import AIAlgorithms
from typing import List
import random


class MinesweeperAPI(MinesweeperBoard):
    """API for interacting with a Minesweeper board, including AI support."""
    def __init__(
        self,
        dimension: int = config.DEFAULT_BOARD_DIMENSION,
        bomb_percentage: float = config.DEFAULT_BOMB_PERCENTAGE,
        revealed: list = [],
        radius: int = config.DEFAULT_AI_RADIUS,
        trainingsdata_amount: int = config.DEFAULT_AI_TRAININGSDATA_AMOUNT,
        include_bomb_count: bool = config.DEFAULT_INCLUDE_BOMB_COUNT,
        include_hidden_count: bool = config.DEFAULT_INCLUDE_HIDDEN_COUNT,
    ):
        super().__init__(dimension, bomb_percentage, revealed)
        self.set_hidden_board()
        self.moves: int = 0
        self.radius: int = radius
        self.trainingsdata_amount: int = trainingsdata_amount
        self.ai = None
        self.has_died: bool = False
        self.include_bomb_count: bool = include_bomb_count
        self.include_hidden_count: bool = include_hidden_count

    def set_hidden_board(self) -> list[list[int]]:
        hidden_board = [[self.HIDDEN] * self.size for _ in range(self.size)]
        self.hidden_board = hidden_board
        return self.hidden_board

    def reveal(self, x: int, y: int, is_initial: bool = True) -> tuple[list[list[int]], bool]:
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
            return self.die()
        elif cell > 0:
            self.moves += 1
            self.hidden_board[y][x] = self.number_board[y][x]
            return self.hidden_board, False
        elif cell == 0:
            self.moves += 1
            self.revealZero(x, y)
            return self.hidden_board, False

    def die(self) -> tuple[list[list[int]], bool]:
        self.last_revealed_count = self.get_revealed_count()
        self.hidden_board = [row[:] for row in self.number_board]
        self.moves += 1
        self.has_died = True
        return self.number_board, True

    def revealZero(self, x: int, y: int) -> None:
        if self.hidden_board[y][x] != self.HIDDEN:
            return
        cell = self.number_board[y][x]
        self.hidden_board[y][x] = cell
        if cell == 0:
            for ny, nx in self.iter_neighborhood(x, y):
                if nx == x and ny == y:
                    continue
                self.revealZero(nx, ny)

    def convert(self, number: int) -> str:
        if number == self.HIDDEN:
            return "□"
        if number == self.BOMB:
            return "*"
        return str(number)

    def get_cell(self, x: int, y: int, board: list[list[int]] = None) -> int:
        if board is None:
            board = self.hidden_board
        return board[y][x]

    def flag(self, x: int, y: int) -> None:
        cell = self.hidden_board[y][x]
        if cell == self.HIDDEN:
            self.hidden_board[y][x] = self.FLAG
        elif cell == self.FLAG:
            self.hidden_board[y][x] = self.HIDDEN

    def get_hidden_cell_count(self) -> int:
        summe = 0
        for row in self.hidden_board:
            for cell in row:
                if cell == self.HIDDEN:
                    summe += 1
        return summe

    def has_won(self, died: bool = False) -> bool:
        if died:
            return False
        has_won = (
            self.get_hidden_cell_count() + self.get_flag_count() - self.bomb_count == 0
        )
        return has_won

    def ended(self) -> bool:
        has_ended = self.has_died or self.has_won()
        return has_ended

    def __str__(self) -> str:
        hidden_board = [
            [self.convert(cell) for cell in row] for row in self.hidden_board
        ]
        return stringify_board(hidden_board)

    def reset(self) -> None:
        if not hasattr(self, "last_revealed_count"):
            self.last_revealed_count = -1
        stats.log(self.has_won(), self.has_died, self.moves, self.bomb_count, self.size, self.last_revealed_count)
        self.moves = 0
        self.set_hidden_board()
        self.has_died = False
        self.last_revealed_count = self.get_revealed_count()

    def safe_game(self, x: int, y: int) -> None:
        radius = self.radius
        trainingsdata_amount = self.trainingsdata_amount
        ai = self.ai
        self.__init__(
            self.size, self.bomb_percentage, [(x, y)], radius, trainingsdata_amount
        )
        self.ai = ai

    def predict(self, coordinates: tuple[int, int]) -> float:
        self.init_ai()
        prediction = self.ai.predict(self, coordinates)[:, 1][0]
        if config.CONSIDER_UNKNOWNS:
            return self.weigh_prediction_unknowns(coordinates, prediction)
        else: 
            return prediction
        
    def weigh_prediction_unknowns(self, coordinates: tuple[int, int], prediction: float) -> float:
            x, y = coordinates
            neighborhood = self.get_out_of_bounds_neighborhood(
                self.hidden_board, x, y, config.NIEGHBORHOOD_RELEVANT
            )
            unknown_count = self.count_element(neighborhood, self.HIDDEN) + self.count_element(neighborhood, self.OUT_OF_BOUNDS)
            max_neighborhood_size = (config.NIEGHBORHOOD_RELEVANT * 2 + 1) ** 2 # determine max possible neighborhood size for normalization
            norm_unknown_count = linNorm(unknown_count, max_neighborhood_size, 0, 1, 0) # Normalize
            uncertainty_weight = config.PREDICTION_UNCERTAINTY_WEIGHT
            confidence = 1 - (norm_unknown_count * uncertainty_weight)
            # Pull uncertain predictions toward 50% (maximum uncertainty)
            return (
                prediction * confidence
                + config.PREDICTION_UNCERTAINTY_CENTER * (1 - confidence)
            )

    def predict_all(self) -> list[list[float]]:
        self.init_ai()

        predictions = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        probabilities_raw = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        hidden_cords = []

        for y, row in enumerate(self.hidden_board):
            for x, cell in enumerate(row):
                if cell == self.HIDDEN:
                    hidden_cords.append((x, y))

        if len(hidden_cords) == 0:
            return predictions

        probabilities = self.ai.predict_many(self, hidden_cords)
        for (x, y), probability in zip(hidden_cords, probabilities):
            if config.CONSIDER_UNKNOWNS:
                p = self.weigh_prediction_unknowns((x, y), probability)
            else:
                p = probability
            predictions[y][x] = round_prediction(p)
            probabilities_raw[y][x] = p

        return predictions, probabilities_raw

    def ai_move(self, flagging: bool = False) -> tuple[int, int] | None:
        predictions, probabilities = self.predict_all()
        smallest = config.PREDICTION_SCALE_MAX
        smallest_coordinates = None
        largest = 0
        largest_coordinates = None
        for y, row in enumerate(probabilities):
            for x, cell in enumerate(row):
                if 0 <= cell <= config.PREDICTION_SCALE_MAX:
                    if cell < smallest:
                        smallest = cell
                        smallest_coordinates = (x, y)
                    if cell > largest:
                        largest = cell
                        largest_coordinates = (x, y)
        if smallest_coordinates is None or largest_coordinates is None:
            return None
        if flagging and config.PREDICTION_SCALE_MAX - largest < smallest:
            if config.VERIFY_FLAG_PLACEMENT and self.get_cell(largest_coordinates[0], largest_coordinates[1], self.number_board) != self.BOMB:
                self.die()
            else:
                self.flag(largest_coordinates[0], largest_coordinates[1])
            return largest_coordinates
        else:
            self.reveal(smallest_coordinates[0], smallest_coordinates[1])
            return smallest_coordinates

    def count_element(self, matrix: list[list[int]], element: int | str) -> int:
        count = 0
        for row in matrix:
            for cell in row:
                if cell == element:
                    count += 1
        return count
    
    def count_elements(self, matrix: list[list[int]], elements: list[int]):
        if matrix is None:
            matrix = self.hidden_board
        count = 0
        for row in matrix:
            for cell in row:
                if cell in elements:
                    count += 1
        return count

    def get_flag_count(self, matrix: list[list[int]] = None) -> int:
        if matrix is None:
            matrix = self.hidden_board
        return self.count_element(matrix, self.FLAG)

    def get_revealed_count(self, matrix: list[list[int]] = None) -> int:
        if matrix is None:
            matrix = self.hidden_board
        return self.count_elements(matrix, range(0, 8))
    
    def is_revealed(self, value: int) -> bool:
        return 0 <= value <= 8
    
    def algo_move(self, coordinates: tuple[int, int], algo_revealed: list) -> None:
        x, y = coordinates
        cell = self.get_cell(x, y)
        if not self.is_revealed(cell):
            return
        neighborhood = self.get_neighborhood(self.hidden_board, x, y, 1)
        hidden_count = self.count_element(neighborhood, self.HIDDEN)
        flag_count = self.count_element(neighborhood, self.FLAG)
        if hidden_count > 0 and hidden_count + flag_count == cell:
            for ny, nx in self.iter_neighborhood(x, y, 1):
                if self.get_cell(nx, ny) == self.HIDDEN:
                    algo_revealed.append((nx, ny))
                    self.flag(nx, ny)
        if flag_count == cell:
            for ny, nx in self.iter_neighborhood(x, y, 1):
                if self.get_cell(nx, ny) == self.HIDDEN:
                    algo_revealed.append((nx, ny))
                    self.reveal(nx, ny)

    def auto_algo(self, algo_revealed: list) -> None:
        while True:
            revealed_before = self.get_revealed_count()
            flagged_before = self.get_flag_count()

            for y, row in enumerate(self.hidden_board):
                for x, cell in enumerate(row):
                    if cell == self.HIDDEN:
                        continue
                    elif self.is_revealed(cell):
                        self.algo_move((x, y), algo_revealed)
            
            if revealed_before == self.get_revealed_count() and flagged_before == self.get_flag_count():
                break

    def random_move(self) -> tuple[int, int] | None:
        hidden_cell_coordinates = []
        for y, row in enumerate(self.hidden_board):
            for x, cell in enumerate(row):
                if cell == self.HIDDEN:
                    hidden_cell_coordinates.append((x, y))
        if len(hidden_cell_coordinates) == 0:
            return None
        random.shuffle(hidden_cell_coordinates)
        x, y = hidden_cell_coordinates[0]
        self.reveal(x, y)
        return (x, y)
    
    def init_ai(self):
        if self.ai is None:
            from minesweeper.ai import MinesweeperAI

            self.ai = MinesweeperAI(
                self.radius,
                self.trainingsdata_amount,
                self.bomb_percentage,
                self.include_bomb_count,
                self.include_hidden_count,
            )
    
    def train(self, method: AIAlgorithms = ""):
        self.init_ai()
        self.ai.train(method)

    def get_ai_type_loaded(self):
        if self.ai:
            return self.ai.model_type_loaded
        return None


if __name__ == "__main__":
    board = MinesweeperAPI()
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
