import random
from interactive import MinesweeperAPI
from sklearn.model_selection import train_test_split

class MinesweeperAI:
    class CONFIG:
        alpha = 0.01 
        loss_threshold = 0.001
        max_steps = 9999

    def __init__(self, radius_neighborhood, trainingsdata_amount, bomb_percentage):
        board_dimension = radius_neighborhood * 2 + 1
        self.weights = [random.random()] * board_dimension**2
        trainingsdata = []
        while len(trainingsdata) < trainingsdata_amount:
            td = getTraingsdata(board_dimension + 2, bomb_percentage, radius_neighborhood)
            if td: trainingsdata.append(td)
        self.trainingsdata = trainingsdata
        
    def train(self):
        for i in range(self.CONFIG.max_steps):
            loss = 999
            if loss < self.CONFIG.loss_threshold:


def getTraingsdata(board_dimension, bomb_percentage, radius):
    safe_cells = [[random.randint(0, board_dimension - 1), random.randint(0, board_dimension - 1)] for _ in range(4)]
    board = MinesweeperAPI(board_dimension, bomb_percentage, safe_cells)
    print(board.stringify_board(board.get_binary_board()))
    for safe_cell in safe_cells:
        board.reveal(safe_cell[0], safe_cell[1])
    print(board)
    min_coordinate_neighborhood_in_bounds = 0 + radius
    max_coordinate_neighborhood_in_bounds = board_dimension - radius - 1
    traindata = []
    for y in range(min_coordinate_neighborhood_in_bounds, max_coordinate_neighborhood_in_bounds):
        for x in range(min_coordinate_neighborhood_in_bounds, max_coordinate_neighborhood_in_bounds):
            if board.hidden_board[y][x] != board.HIDDEN:
                continue
            revealed_cells = 0
            for ny, nx in board.iter_neighborhood(x, y, radius):
                if board.hidden_board[ny][nx] >= 0:
                    revealed_cells += 1
            if revealed_cells / (radius * 2 + 1)**2 > 0.25:
                data = {
                    "coordinates": [x, y],
                    "solution": board.hidden_board[y][x],
                    "neighborhood": board.get_neighborhood(board.hidden_board, x, y, radius)
                }
                traindata.append(data)
    if traindata: return traindata[random.randint(0, len(traindata) - 1)]
    return traindata


#print(getTraingsdata(11, 15, 2))

MinesweeperAI(2, 5, 15)