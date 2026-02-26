import pygame
from ui.config import config
from minesweeper.generator import MinesweeperBoard

class Renderer:
    def __init__(self):
        self.board_x = 0
        self.board_y = 0
        self.reset_rect = pygame.Rect(0, 0, 0, 0)
        self.ai_solve_rect = pygame.Rect(0, 0, 0, 0)

    def draw_cell(self, surface, left, top, content):
        if content in config.COLOR_MAP.keys():
            color = config.COLOR_MAP[content]
        else:
            color = (0, 0, 0)

        rect = pygame.Rect(left, top, config.CELL_WIDTH, config.CELL_WIDTH)
        display = None
        if content == MinesweeperBoard.HIDDEN:
            background = config.BACKGROUND_HIDDEN
        elif content == MinesweeperBoard.BOMB:
            background = config.BACKGROUND_BOMB
            display = config.BOMB_IMG
        elif content == MinesweeperBoard.FLAG:
            background = config.BACKGROUND_HIDDEN
            display = config.FLAG_IMG
        else:
            background = config.BACKGROUND_REVEALED
            if content > 0:
                display = config.FONT.render(str(content), True, color)

        pygame.draw.rect(surface, background, rect)
        pygame.draw.rect(surface, config.BORDER_COLOR, rect, config.BORDER_WIDTH) # Border

        if display:
            display_rect = display.get_rect(center=rect.center)
            surface.blit(display, display_rect)

    def draw_board(self, surface, matrix):
        origin_x = (config.WIDTH - (config.CELL_WIDTH * config.BOARD_SIZE))
        origin_y = (config.HEIGHT - (config.CELL_HEIGHT * config.BOARD_SIZE)) // 2
        for y in range(config.BOARD_SIZE):
            for x in range(config.BOARD_SIZE):
                left = origin_x + x * config.CELL_WIDTH
                top = origin_y + y * config.CELL_HEIGHT

                self.draw_cell(surface, left, top, matrix[y][x])
        self.board_x = origin_x
        self.board_y = origin_y
    
    def draw_menu(self, surface):
        menu_width = self.board_x
        margin = 10
        button_height = config.WIDTH/12
        button_width = menu_width - 2 * margin
        self.reset_rect = self.draw_button(margin, button_height * 1, button_width, button_height, "RESET", surface)
        self.ai_solve_rect = self.draw_button(margin, button_height * 2.5, button_width, button_height, "AI SOLVE", surface)
        self.quit_rect = self.draw_button(margin, config.HEIGHT - margin - button_height, button_width, button_height, "QUIT", surface)


    def draw_button(self, left, top, width, height, text, surface):
        btn_rect = pygame.rect.Rect(left, top, width, height)
        pygame.draw.rect(surface, config.BACKGROUND, btn_rect)
        pygame.draw.rect(surface, config.BORDER_COLOR, btn_rect, config.BORDER_WIDTH)
        txt_surface = config.FONT.render(text, True, config.COLOR)
        txt_rect = txt_surface.get_rect(center=btn_rect.center)
        surface.blit(txt_surface, txt_rect)
        return btn_rect