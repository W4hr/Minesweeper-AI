import random
from minesweeper.interactive import MinesweeperAPI
from minesweeper.config import config
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import mean_squared_error, root_mean_squared_error
from global_config import AIAlgorithms
import numpy as np
import time

ENCODE_VALUES = [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
VAL_TO_IDX = {v: i for i, v in enumerate(ENCODE_VALUES)}

def encode_neighborhood(flat_neighborhood: np.ndarray) -> list[int]:
    idx = np.array([VAL_TO_IDX[int(v)] for v in flat_neighborhood], dtype=int)
    return np.eye(len(ENCODE_VALUES), dtype=int)[idx].flatten().tolist()

def build_features(
    board: MinesweeperAPI,
    coordinates: tuple[int, int],
    radius: int,
    include_bomb_count: bool,
    include_hidden_count: bool,
    include_revealed_count: bool,
    one_hot_encoding: bool,
) -> np.ndarray:
    x, y = coordinates
    neighborhood = board.get_out_of_bounds_neighborhood(board.hidden_board, x, y, radius)
    additional_data = []
    if include_bomb_count:
        additional_data.append(board.bomb_count)
    if include_hidden_count:
        additional_data.append(board.count_elements(neighborhood, board.HIDDEN))
    if include_revealed_count:
        additional_data.append(board.get_revealed_count(neighborhood))

    flat_neighborhood = np.asarray(neighborhood).flatten()
    if one_hot_encoding:
        features = encode_neighborhood(flat_neighborhood)
    else:
        features = flat_neighborhood.tolist()

    return np.asarray(features + additional_data)

class MinesweeperAI:
    """AI for solving Minesweeper games using logistic regression."""
    def __init__(
        self,
        radius_neighborhood: int,
        trainingsdata_amount: int = config.DEFAULT_AI_TRAININGSDATA_AMOUNT,
        bomb_percentage: int = config.DEFAULT_BOMB_PERCENTAGE,
        include_bomb_count: bool = config.DEFAULT_INCLUDE_BOMB_COUNT,
        include_hidden_count: bool = config.DEFAULT_INCLUDE_HIDDEN_COUNT,
        include_revealed_count: bool = config.DEFAULT_INCLUDE_REVEALED_COUNT,
    ):
        self.radius: int = radius_neighborhood
        self.model: LogisticRegression | None = None
        self.trainingsdata_amount: int = trainingsdata_amount

        self.include_bomb_count: bool = include_bomb_count
        self.include_hidden_count: bool = include_hidden_count
        self.include_revealed_count: bool = include_revealed_count
        self.bomb_percentage: float = bomb_percentage

        self.model_type_loaded = None
        self.dataset_method = None
        self.one_hot_encoding: bool = config.ONE_HOT_ENCODING

        self._prepare_data_for_method(config.FALLBACK_METHOD)

    def _resolve_one_hot_encoding(self, method: AIAlgorithms) -> bool:
        if method == AIAlgorithms.LOGISTIC_REGRESSION:
            return config.LOGREG_ONE_HOT_ENCODING
        if method == AIAlgorithms.RANDOM_FOREST:
            return config.RF_ONE_HOT_ENCODING
        if method == AIAlgorithms.GRADIENT_BOOSTING:
            return config.GB_ONE_HOT_ENCODING
        return config.ONE_HOT_ENCODING

    def _prepare_data_for_method(self, method: AIAlgorithms) -> None:
        board_dimension = self.radius * 2 + config.BOARD_DIMENSION_PADDING
        X = []
        Y = []
        self.one_hot_encoding = self._resolve_one_hot_encoding(method)

        print("Generating trainingsdata...")
        start_data_gen = time.time()
        while len(X) < self.trainingsdata_amount:
            samples = get_trainingsdata(
                board_dimension,
                self.bomb_percentage,
                self.radius,
                self.include_bomb_count,
                self.include_hidden_count,
                self.include_revealed_count,
                self.one_hot_encoding,
            )
            for x_sample, y_sample in samples:
                if len(X) < self.trainingsdata_amount:
                    X.append(x_sample)
                    Y.append(y_sample)
                else:
                    break
        end_data_gen = time.time()
        self.data_generation_seconds = end_data_gen - start_data_gen
        print(f"Successfully generated trainingsdata in {self.data_generation_seconds}")

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
        self.dataset_method = method
        
    def train(self, method: AIAlgorithms = config.FALLBACK_METHOD) -> None:
        if not isinstance(method, AIAlgorithms):
            method = config.FALLBACK_METHOD

        if self.dataset_method != method:
            self._prepare_data_for_method(method)

        self.method = method
        if method == AIAlgorithms.LOGISTIC_REGRESSION:
            self.train_logistic_regression()
        if method == AIAlgorithms.RANDOM_FOREST:
            self.train_random_forest()
        if method == AIAlgorithms.GRADIENT_BOOSTING:
            self.train_gradient_boosting()

    def fit_model(self, model: LogisticRegression | RandomForestClassifier | GradientBoostingClassifier):
        model._parameter_constraints
        print("Training Model")
        start_train = time.time()
        model.fit(self.X_train, self.y_train)
        end_train = time.time()
        self.model_training_seconds = end_train - start_train
        print(f"Model trained in {self.model_training_seconds}")
        y_pred = model.predict(self.X_test)
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        self.mse = mean_squared_error(self.y_test, y_pred)
        self.rmse = root_mean_squared_error(self.y_test, y_pred)
        try:
            self.weights = model.coef_
            self.bias = model.intercept_
        except:
            pass
        self.model = model
        from minesweeper.stats import stats
        stats.log_training(
            self.data_generation_seconds,
            self.model_training_seconds,
            len(self.X_train) + len(self.X_test),
            self.radius,
            self.bomb_percentage,
            self.include_bomb_count,
            self.include_hidden_count,
            self.include_revealed_count
        )


    def train_logistic_regression(self) -> None:
        model = LogisticRegression(
            random_state=config.RANDOM_STATE,
            class_weight=config.LOGREG_CLASS_WEIGHT,
            max_iter=config.LOGREG_MAX_ITER,
        )
        self.fit_model(model)
        self.model_type_loaded = AIAlgorithms.LOGISTIC_REGRESSION

    def train_random_forest(self) -> None:
        model = RandomForestClassifier(
            random_state=config.RANDOM_STATE,
            n_estimators=config.RF_N_ESTIMATORS,
            max_depth=config.RF_MAX_DEPTH,
            min_samples_split=config.RF_MIN_SAMPLES_SPLIT,
            min_samples_leaf=config.RF_MIN_SAMPLES_LEAF,
            class_weight=config.RF_CLASS_WEIGHT,
            n_jobs=config.RF_N_JOBS,
        )
        self.fit_model(model)
        self.model_type_loaded = AIAlgorithms.RANDOM_FOREST

    def train_gradient_boosting(self) -> None:
        model = GradientBoostingClassifier(
            random_state=config.RANDOM_STATE,
            n_estimators=config.GB_N_ESTIMATORS,
            max_depth=config.GB_MAX_DEPTH,
            min_samples_split=config.GB_MIN_SAMPLES_SPLIT,
            min_samples_leaf=config.GB_MIN_SAMPLES_LEAF,
            learning_rate=config.GB_LEARNING_RATE,
            subsample=config.GB_SUBSAMPLE
        )
        self.fit_model(model)
        self.model_type_loaded = AIAlgorithms.GRADIENT_BOOSTING

    def _build_features(self, board: MinesweeperAPI, coordinates: tuple[int, int]):
        return build_features(
            board,
            coordinates,
            self.radius,
            self.include_bomb_count,
            self.include_hidden_count,
            self.include_revealed_count,
            self.one_hot_encoding,
        )

    
    def predict(self, board: MinesweeperAPI, coordinates: tuple[int, int]) -> np.ndarray:
        self.init_ai()
        features = self._build_features(board, coordinates)
        test_vector = features.reshape(1, -1)
        return self.model.predict_proba(test_vector)
    
    def predict_many(self, board: MinesweeperAPI, coordinates_list: list[tuple[int, int]]):
        if len(coordinates_list) == 0:
            return np.array([], dtype=float)
        self.init_ai()

        X_batch = [self._build_features(board, cords) for cords in coordinates_list]
        X_batch = np.asarray(X_batch)
        probs = self.model.predict_proba(X_batch)[:, 1]
        return probs

    def init_ai(self):
        if self.model is None:
            self.train()

def get_trainingsdata(
    board_dimension: int,
    bomb_percentage: float,
    radius: int,
    include_bomb_count: bool,
    include_hidden_count: bool,
    include_revealed_count: bool,
    one_hot_encoding: bool,
) -> list[tuple[list[float], int]]:
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
    if config.TRAININGSDATA_ALGO_REVEAL:
        if random.random() < config.PERCENTAGE_ALGO_REVEAL:
            board.auto_algo([])
    traindata = []
    neighborhood_size = (radius * 2 + 1)**2
    
    for y in range(board_dimension):
        for x in range(board_dimension):
            if board.hidden_board[y][x] != board.HIDDEN:
                continue

            immediate_neighborhood_revealed = 0
            for ny, nx in board.iter_neighborhood(x, y, 1):
                if board.hidden_board[ny][nx] >= 0:
                    immediate_neighborhood_revealed += 1

            if config.MIN_REVEALED_NEIGHBORS > immediate_neighborhood_revealed:
                continue
            
            revealed_cells = 0
            for ny, nx in board.iter_neighborhood(x, y, radius):
                if board.hidden_board[ny][nx] >= 0:
                    revealed_cells += 1
            
            if revealed_cells / neighborhood_size > config.TRAINING_MIN_REVEALED_RATIO:
                features = build_features(
                    board,
                    (x, y),
                    radius,
                    include_bomb_count,
                    include_hidden_count,
                    include_revealed_count,
                    one_hot_encoding,
                ).tolist()
                data = (features, board.binary_vector[y * board_dimension + x])
                traindata.append(data)
    
    return traindata

if __name__ == "__main__":
    #print(getTraingsdata(11, 15, 2))

    ai = MinesweeperAI(config.DEFAULT_AI_RADIUS)
    ai.train()
    board = MinesweeperAPI()
    print(ai.X_test)
    print()