import random
from minesweeper.interactive import MinesweeperAPI
from minesweeper.config import config
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, root_mean_squared_error
import numpy as np
import time

class MinesweeperAI:
    def __init__(
        self,
        radius_neighborhood,
        trainingsdata_amount=config.DEFAULT_AI_TRAININGSDATA_AMOUNT,
        bomb_percentage=config.DEFAULT_BOMB_PERCENTAGE,
        include_bomb_count=config.DEFAULT_INCLUDE_BOMB_COUNT,
        include_hidden_count=config.DEFAULT_INCLUDE_HIDDEN_COUNT,
        include_revealed_count=config.DEFAULT_INCLUDE_REVEALED_COUNT,
    ):
        board_dimension = radius_neighborhood * 2 + config.BOARD_DIMENSION_PADDING
        X = [] # Input
        Y = [] # Expected Ouput
        print("Generating trainingsdata...")
        start_data_gen = time.time()
        while len(X) < trainingsdata_amount:
            samples = getTraingsdata(board_dimension, bomb_percentage, radius_neighborhood, include_bomb_count, include_hidden_count, include_revealed_count)
            for x_sample, y_sample in samples:
                if len(X) < trainingsdata_amount:
                    X.append(x_sample)
                    Y.append(y_sample)
                else:
                    break
        end_data_gen = time.time()
        print(f"Successfully generated trainingsdata in {end_data_gen - start_data_gen}")
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            Y,
            test_size=config.TRAIN_TEST_SPLIT_TEST_SIZE,
            random_state=config.TRAIN_TEST_SPLIT_RANDOM_STATE,
            shuffle=config.TRAIN_TEST_SPLIT_SHUFFLE,
        )
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.radius = radius_neighborhood
        self.model = None

        self.include_bomb_count = include_bomb_count
        self.include_hidden_count = include_hidden_count
        self.include_revealed_count = include_revealed_count
        
    def train(self):
        model = LogisticRegression(
            random_state=config.LOGREG_RANDOM_STATE,
            class_weight=config.LOGREG_CLASS_WEIGHT,
            max_iter=config.LOGREG_MAX_ITER,
        )
        print("Training Model")
        start_train = time.time()
        model.fit(self.X_train, self.y_train)
        end_train = time.time()
        print(f"Model trained in {end_train - start_train}")
        y_pred = model.predict(self.X_test)
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        self.mse = mean_squared_error(self.y_test, y_pred)
        self.rmse = root_mean_squared_error(self.y_test, y_pred)
        self.weights = model.coef_
        self.bias = model.intercept_
        self.model = model
    
    def predict(self, board: MinesweeperAPI, coordinates):
        if self.model is None:
            self.train()
        x, y = coordinates
        neighborhood = board.get_out_of_bounds_neighborhood(board.hidden_board, x, y, self.radius)
        additional_data = []
        if self.include_bomb_count:
            additional_data.append(board.bomb_count)
        if self.include_hidden_count:
            additional_data.append(board.count_elements(neighborhood, board.HIDDEN))
        if self.include_revealed_count:
            additional_data.append(board.get_revealed_count(neighborhood))

        flat_neighborhood = np.asarray(neighborhood).flatten().tolist()
        test_vector = np.asarray(flat_neighborhood + additional_data).reshape(1, -1)
        return self.model.predict_proba(test_vector)

def getTraingsdata(
    board_dimension,
    bomb_percentage,
    radius,
    include_bomb_count,
    include_hidden_count,
    include_revealed_count,
):
    safe_cells = [
        [random.randint(0, board_dimension - 1), random.randint(0, board_dimension - 1)]
        for _ in range(config.TRAINING_SAFE_CELLS)
    ]
    new_bomb_percentage = np.random.normal(
        bomb_percentage, bomb_percentage / config.TRAINING_BOMB_PERCENTAGE_STD_DIVISOR, 1
    )[0]
    board = MinesweeperAPI(board_dimension, new_bomb_percentage, safe_cells)
    for safe_cell in safe_cells:
        board.reveal(safe_cell[0], safe_cell[1])
    
    traindata = []
    neighborhood_size = (radius * 2 + 1)**2
    
    for y in range(board_dimension):
        for x in range(board_dimension):
            if board.hidden_board[y][x] != board.HIDDEN:
                continue
            
            revealed_cells = 0
            for ny, nx in board.iter_neighborhood(x, y, radius):
                if board.hidden_board[ny][nx] >= 0:
                    revealed_cells += 1
            
            if revealed_cells / neighborhood_size > config.TRAINING_MIN_REVEALED_RATIO:
                neighborhood = board.get_out_of_bounds_neighborhood(board.hidden_board, x, y, radius)
                additional_data = []
                if include_bomb_count:
                    additional_data.append(board.bomb_count)
                if include_hidden_count:
                    additional_data.append(board.count_elements(neighborhood, board.HIDDEN))
                if include_revealed_count:
                    additional_data.append(board.get_revealed_count(neighborhood))
                
                flat_neighborhood = np.asarray(neighborhood).flatten().tolist()
                data = (flat_neighborhood + additional_data, board.binary_vector[y * board_dimension + x])
                traindata.append(data)
    
    return traindata

if __name__ == "__main__":
    #print(getTraingsdata(11, 15, 2))

    ai = MinesweeperAI(5, 50, 15)
    ai.train()
    board = MinesweeperAPI(2)
    print(ai.X_test)
    print()