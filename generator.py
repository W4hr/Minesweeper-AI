import random as rd
import math
from typing import List

def bordered(text):
    """
    Surrounds text with a box
    
    :param text: the Minesweeper board to be surrounded
    """
    lines = text.splitlines()
    width = max(len(s) for s in lines)
    res = ['┌' + '─' * (width+2) + '┐']
    for s in lines:
        res.append('│ ' + s.ljust(width) + ' │')
    res.append('└' + '─' * (width+2) + '┘')
    return '\n'.join(res)


class MinesweeperBoard:
    """
    Generates board with bombs on initialization
    """

    BOMB = -2
    OUT_OF_BOUNDS = -4

    def __init__(self, dimension: int = 5, bomb_percentage: float = 15, revealed = None):
        if revealed is None:
            revealed = []
        # revealed = list(set(revealed))
        
        bomb_count = math.ceil((dimension**2) * (bomb_percentage/100))
        binary_vector = [1] * bomb_count + [0] * (dimension**2 - bomb_count - len(revealed))
        rd.shuffle(binary_vector)

        revealed = sorted(revealed, key=lambda r:(r[1], r[0]))
        for revealed_coordinates in revealed:
            x, y = revealed_coordinates
            if not (0 <= x < dimension and 0 <= y < dimension): raise IndexError
            binary_vector.insert(y * dimension + x, 0)

        self.binary_vector = binary_vector
        self.size = dimension
        self._generate_number_vector()
        self.number_board = self.get_number_board()

    def _generate_number_vector(self, area_around = 1):
        """
        Converts binary matrix to a matrix showing the amount of bombs in the surrounding squares
        
        :param area_around: defines area around a cell counting towards the bomb count of this cell
        """
        matrix = self.get_binary_board()
        number_vector = []
        for y, row in enumerate(matrix):
            for x, entry in enumerate(row):
                if entry == 1:
                    number_vector.append(self.BOMB)
                    continue
                count = 0
                for ny, nx in self.iter_neighborhood(x, y, area_around):
                    count += matrix[ny][nx]
                number_vector.append(count)
        self.number_vector = number_vector
        return number_vector

    def get_neighborhood(self, matrix, x, y, area_around = 1):
        """
        Returns neighborhood around `matrix(x,y)`
        
        :param matrix: Matrix of which to return the neighborhood of
        :param x: x coordinate of the center of the neighborhood
        :param y: y coordinate of the center of the neighborhood
        :param area_around: the distance to the center of the neighborhood
        """

        neighborhood = []
        current_row = None
        for ny, nx in self.iter_neighborhood(x, y, area_around):
            if ny != current_row:
                neighborhood.append([])
                current_row = ny
            neighborhood[-1].append(matrix[ny][nx])

        return neighborhood
    
    def get_out_of_bounds_neighborhood(self, matrix, x, y, area_around = 1):
        x_start = x - area_around
        x_end = x + area_around
        y_start = y - area_around
        y_end = y + area_around
        neighborhood = []
        for y in range(y_start, y_end + 1):
            new_row = []
            for x in range(x_start, x_end + 1):
                if y < 0 or y > self.size - 1 or x < 0 or x > self.size - 1:
                    new_row.append(self.OUT_OF_BOUNDS)
                else:
                    new_row.append(matrix[y][x])
            neighborhood.append(new_row)
        return neighborhood

    def iter_neighborhood(self, x, y, area_around = 1):
        """
        returns iteratively the indexes of the neighborhood around `x` and `y`
        
        :param x: x coordinate of the center of the neighborhood
        :param y: y coordinate of the center of the neighborhood
        :param area_around: the distance to the center of the neighborhood
        """
        y_start = max(0, y - area_around)
        y_end   = min(self.size - 1, y + area_around)
        x_start = max(0, x-area_around)
        x_end   = min(self.size - 1, x + area_around)
        y_range = range(y_start, y_end + 1)
        x_range = range(x_start, x_end + 1)
        for ny in y_range:
            for nx in x_range:
                yield ny, nx


    # User-Interface-Helper-Functions
    def get_binary_board(self):
        return self.to_board(self.binary_vector)
    
    def get_number_board(self):
        if not hasattr(self, "number_vector"):
            self._generate_number_vector()
        return self.to_board(self.number_vector)

    def to_board(self, vector: List[int]):
        return [vector[self.size * x: self.size * x + self.size] for x in range(self.size)]
    
    def stringify_board(self, board: List[List[int]], bomb = None):
        joined_board = ""
        if bomb is None:
            bomb = self.BOMB
        for i in board:
            joined_board += " ".join([str(j) if j != bomb else "*" for j in i]) + "\n"
        return bordered(joined_board)

    def __str__(self):
        return self.stringify_board(self.number_board)
    
if __name__ == "__main__":
    example = MinesweeperBoard(10)
    print(example.stringify_board(example.get_binary_board(), 1))
    print(example)
    print(example.stringify_board(example.get_neighborhood(example.get_number_board(), 4, 7, 2)))