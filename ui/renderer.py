import pygame
from ui.config import config
from minesweeper.generator import MinesweeperBoard
from typing import List, Tuple
from minesweeper.utils import probability_to_color
from global_config import AIAlgorithms

class Renderer:
    """Handles rendering the Minesweeper board and UI elements using Pygame."""
    def __init__(self):
        self.board_x = 0
        self.board_y = 0
        self.reset_rect = pygame.Rect(0, 0, 0, 0)
        self.ai_solve_rect = pygame.Rect(0, 0, 0, 0)

    def draw_cell(self, surface: pygame.Surface, left: int, top: int, content: int | float, font: pygame.font.Font = config.FONT, cell_type: str = config.BOARD_CELL) -> None:
        rect = pygame.Rect(left, top, config.CELL_WIDTH, config.CELL_WIDTH)

        if cell_type == config.PREDICTION_CELL:
            prob_color = probability_to_color(float(content))
            pygame.draw.rect(surface, prob_color, rect, config.BORDER_WIDTH * 2)
            display = font.render(f"{float(content):.0f}", True, config.COLOR)
            display_rect = display.get_rect(center=rect.center)
            surface.blit(display, display_rect)
            return

        if content in config.COLOR_MAP.keys() and cell_type != config.PREDICTION_CELL:
            color = config.COLOR_MAP[content]
        else:
            color = (0, 0, 0)

        BORDER_COLOR = config.BORDER_COLOR
        if cell_type == config.PREDICTION_CELL:
            BORDER_COLOR = probability_to_color(float(content))

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
                display = font.render(str(content), True, color)

        pygame.draw.rect(surface, background, rect)
        pygame.draw.rect(surface, BORDER_COLOR, rect, config.BORDER_WIDTH) # Border

        if display:
            display_rect = display.get_rect(center=rect.center)
            surface.blit(display, display_rect)

    def draw_board(self, surface: pygame.Surface, matrix: list[list[int]]) -> None:
        origin_x = (config.WIDTH - (config.CELL_WIDTH * config.BOARD_SIZE))
        origin_y = (config.HEIGHT - (config.CELL_HEIGHT * config.BOARD_SIZE)) // 2
        for y in range(config.BOARD_SIZE):
            for x in range(config.BOARD_SIZE):
                left = origin_x + x * config.CELL_WIDTH
                top = origin_y + y * config.CELL_HEIGHT

                self.draw_cell(surface, left, top, matrix[y][x])
        self.board_x = origin_x
        self.board_y = origin_y
    
    def draw_menu(self, surface: pygame.Surface, has_won: bool, has_died: bool, bomb_count: int, show_log_length: bool, games_completed: int, loaded_model: AIAlgorithms) -> None:
        menu_width = self.board_x
        margin = config.MENU_MARGIN
        button_height = config.WIDTH/25
        button_width = menu_width - 2 * margin

        status_text = "playing"
        if has_won:
            status_text = "you won"
        if has_died:
            status_text = "you died"
        self.status_rect = self.draw_button(margin, button_height * 0 + margin * 1, (button_width - margin)/2, button_height, status_text, surface, config.GAME_STATUS_BACKGROUND, 20)
        if not show_log_length:
            bomb_count_text = f"{bomb_count}"
        else:
            bomb_count_text = f"{games_completed}"
        self.bomb_count_rect = self.draw_button(margin*2 + (button_width - margin)/2, button_height * 0 + margin * 1, (button_width - margin)/2 , button_height, bomb_count_text, surface, config.BOMB_COUNT_BACKGROUND, 20)
        self.reset_rect = self.draw_button(margin, button_height * 1 + margin * 2, button_width, button_height, "RESET", surface)
        half_button_width = button_width / 2 - margin / 2

        def button_row(desired_row: int) -> int | float:
            return button_height * desired_row + margin * (desired_row + 1)
        
        def button_column(desired_column: int) -> int | float:
            return margin * desired_column + half_button_width * (desired_column - 1)

        self.train_logistic_rect = self.draw_button(button_column(1), button_row(2), half_button_width, button_height, "LOGISTIC", surface, config.GREEN if loaded_model == AIAlgorithms.LOGISTIC_REGRESSION else config.BACKGROUND)
        self.train_random_forest = self.draw_button(button_column(2), button_row(2), half_button_width, button_height, "RAND FOREST", surface, config.GREEN if loaded_model == AIAlgorithms.RANDOM_FOREST else config.BACKGROUND)

        self.train_gradient_boosted = self.draw_button(button_column(1), button_row(3), half_button_width, button_height, "GRADIENT", surface, config.GREEN if loaded_model == AIAlgorithms.GRADIENT_BOOSTING else config.BACKGROUND)
        self.train_convolutional_neural_network = self.draw_button(button_column(2), button_row(3), half_button_width, button_height, "CNN", surface, config.GREEN if loaded_model == AIAlgorithms.CNN else config.BACKGROUND)

        self.ai_pred_rect = self.draw_button(button_column(1), button_row(4), half_button_width, button_height, "AI PREDICT", surface)
        self.auto_pred_rect = self.draw_button(button_column(2), button_row(4), half_button_width, button_height, "AUTO-PREDICT", surface)

        self.ai_move_rect = self.draw_button(button_column(1), button_row(5), half_button_width, button_height, "AI MOVE", surface)
        self.ai_solve_rect = self.draw_button(button_column(2), button_row(5), half_button_width, button_height, "AI SOLVE", surface)

        self.algo_move_rect = self.draw_button(button_column(1), button_row(6), half_button_width, button_height, "ALGO MOVE", surface)
        self.algo_solve_rect = self.draw_button(button_column(2), button_row(6), half_button_width, button_height, "ALGO SOLVE", surface)
        
        self.random_move_rect = self.draw_button(button_column(1), button_row(7), half_button_width, button_height, "RANDOM MOVE", surface)
        self.random_solve_rect = self.draw_button(button_column(2), button_row(7), half_button_width, button_height, "RANDOM SOLVE", surface)

        self.dual_solve_rect = self.draw_button(button_column(1), button_row(8), half_button_width, button_height, "HYBRID SOLVE", surface)
        self.hybrid_random_solve_rect = self.draw_button(button_column(2), button_row(8), half_button_width, button_height, "HYBRID RANDOM", surface)

        self.quit_rect = self.draw_button(margin, config.HEIGHT - margin - button_height, button_width, button_height, "QUIT", surface)


    def draw_button(self, left: int, top: int, width: int, height: int, text: str, surface: pygame.Surface, background_color: tuple[int, int, int] = config.BACKGROUND, border_radius: int = -1) -> pygame.Rect:
        """Draws a button"""
        btn_rect = pygame.rect.Rect(left, top, width, height)
        pygame.draw.rect(surface, background_color, btn_rect, border_radius=border_radius)
        pygame.draw.rect(surface, config.BORDER_COLOR, btn_rect, config.BORDER_WIDTH, border_radius=border_radius)
        txt_surface = config.BUTTON_FONT.render(text, True, config.COLOR)
        txt_rect = txt_surface.get_rect(center=btn_rect.center)
        surface.blit(txt_surface, txt_rect)
        return btn_rect
    
    def draw_cursor(self, mode: int, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        if mode == config.CLICK_AI_PRED:
            pygame.mouse.set_visible(False)
            cursor_img_rect = config.WAND_IMG.get_rect()
            cursor_img_rect.center = pos
            surface.blit(config.WAND_IMG, cursor_img_rect)
            self.ai_cursor_rect = cursor_img_rect
        elif mode == config.CLICK_ALGO_PRED:
            pygame.mouse.set_visible(False)
            cursor_img_rect = config.ROBOT_IMG.get_rect()
            cursor_img_rect.center = pos
            surface.blit(config.ROBOT_IMG, cursor_img_rect)
            self.algo_cursor_rect = cursor_img_rect
        elif mode == config.CLICK_FORBIDDEN:
            pygame.mouse.set_visible(True)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_NO)
        else:
            pygame.mouse.set_visible(True)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    
    def draw_predictions(self, surface: pygame.Surface, matrix: list[list[float]]) -> None:
        for y, row in enumerate(matrix):
            for x, cell in enumerate(row):
                if cell != config.UNKNOWN_PROB:
                    left = self.board_x + x * config.CELL_WIDTH
                    top = self.board_y + y * config.CELL_HEIGHT
                    self.draw_cell(surface, left, top, cell, config.SMALL_FONT, config.PREDICTION_CELL)

    def draw_border(self, surface: pygame.Surface, x: int, y: int, border_color: tuple[int, int, int] = config.BORDER_COLOR, border_width: int = config.BORDER_WIDTH) -> None:
        left = self.board_x + x * config.CELL_WIDTH
        top = self.board_y + y * config.CELL_HEIGHT
        rect = pygame.Rect(left, top, config.CELL_WIDTH, config.CELL_WIDTH)
        pygame.draw.rect(surface, border_color, rect, border_width) # Border

    def draw_revealed(self, surface: pygame.Surface, ai_revealed: list[tuple[int, int]], algo_revealed: list[tuple[int, int]]) -> None:
        for revealed in ai_revealed:
            x, y = revealed
            self.draw_border(surface, x, y, config.AI_SOLVED_BORDER_COLOR, config.BORDER_WIDTH * 3)
        for revealed in algo_revealed:
            x, y = revealed
            self.draw_border(surface, x, y, config.ALGO_SOLVED_BORDER_COLOR, config.BORDER_WIDTH * 3)