from enum import Enum

class GlobalConfig:
    BOARD_SIZE = 10
    BOMB_PERCENTAGE = 15

class AIAlgorithms(Enum):
    RANDOM_FOREST = "RANDOM_FOREST"
    LOGISTIC_REGRESSION = "LOGISTIC_REGRESSION"
    GRADIENT_BOOSTING = "GRADIENT_BOOSTING"
    CNN = "CONVOLUTIONAL_NEURAL_NETWORK"

global_config = GlobalConfig()