import random
from minesweeper.interactive import MinesweeperAPI
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, root_mean_squared_error
import numpy as np

class MinesweeperAI:
    def __init__(self, radius_neighborhood, trainingsdata_amount, bomb_percentage):
        board_dimension = radius_neighborhood * 2 + 1
        X = [] # Input
        Y = [] # Expected Ouput
        while len(X) < trainingsdata_amount:
            result = getTraingsdata(board_dimension + 2, bomb_percentage, radius_neighborhood)
            if len(result) == 0: continue
            x, y = result
            X.append(x)
            Y.append(y)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42, shuffle=True)
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        
    def train(self):
        model = LogisticRegression()
        model.fit(self.X_train, self.y_train)
        y_pred = model.predict(self.X_test)
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        self.mse = mean_squared_error(self.y_test, y_pred)
        self.rmse = root_mean_squared_error(self.y_test, y_pred)
        self.weights = model.coef_
        self.bias = model.intercept_
        self.model = model


def getTraingsdata(board_dimension, bomb_percentage, radius):
    safe_cells = [[random.randint(0, board_dimension - 1), random.randint(0, board_dimension - 1)] for _ in range(6)]
    board = MinesweeperAPI(board_dimension, bomb_percentage, safe_cells)
    for safe_cell in safe_cells:
        board.reveal(safe_cell[0], safe_cell[1])
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
                data = (np.asarray(board.get_neighborhood(board.hidden_board, x, y, radius)).flatten(), board.binary_vector[y * board_dimension + x])
                traindata.append(data)
    if traindata: 
        result = traindata[random.randint(0, len(traindata) - 1)]
        return result
    return traindata


#print(getTraingsdata(11, 15, 2))

ai = MinesweeperAI(5, 50, 15)
ai.train()
board = MinesweeperAPI(2)
print(ai.X_test)
print()