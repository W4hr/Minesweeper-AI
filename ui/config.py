import pygame

class Config:
    # META
    FPS = 60
    BOARD_SIZE = 10
    REVEAL_BUTTON = 1 # Left click
    FLAG_BUTTON = 3 # Right click

    # CONTENT
    # SIZING
    WIDTH = 1200
    HEIGHT = 800
    CELL_HEIGHT = 40
    CELL_WIDTH = 40

    BORDER_WIDTH = 1

    # STYLING
    COLOR_MAP = {
        1: (41, 121, 255),
        2: (0, 200, 83),
        3: (255, 23, 68),
        4: (101, 31, 255),
        5: (255, 145, 0),
        6: (0, 184, 212),
        7: (62, 39, 35),
        8: (55, 71, 79)
    }
    BACKGROUND_HIDDEN = (180, 180, 180)
    BACKGROUND_REVEALED = (210, 210, 210)
    BACKGROUND_BOMB = (255, 0, 0)
    BACKGROUND = (180, 180, 180)
    BORDER_COLOR = (0, 0, 0)
    COLOR = (0, 0, 0)

    def __init__(self):
        pygame.init()
        self.CELL_HEIGHT = min(self.HEIGHT, self.WIDTH) / self.BOARD_SIZE
        self.CELL_WIDTH = self.CELL_HEIGHT

        self.BOMB_IMG = pygame.image.load("ui/graphics/bomb.png")
        self.BOMB_IMG = pygame.transform.scale(self.BOMB_IMG, (int(self.CELL_WIDTH * 0.8), int(self.CELL_HEIGHT * 0.8)))

        self.FLAG_IMG = pygame.image.load("ui/graphics/flag.png")
        self.FLAG_IMG = pygame.transform.scale(self.FLAG_IMG, (int(self.CELL_WIDTH * 0.8), int(self.CELL_HEIGHT * 0.8)))

        self.FONT = pygame.font.Font("ui/fonts/Minecraft.ttf", int(self.CELL_HEIGHT * 0.8))


config = Config()