import pygame
from ui.config import config
import sys
import time
from ui.renderer import Renderer
from minesweeper.interactive import MinesweeperAPI
from minesweeper.ai import MinesweeperAI

from minesweeper.utils import stringify_board

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("MinesweeperAI")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer()
        self.board = MinesweeperAPI(config.BOARD_SIZE)
        self.click_mode = config.CLICK_NORMAL
        self.ai = MinesweeperAI(5, 500)
        self.reset_predictions()

    def reset_predictions(self):
        self.predictions = [[config.UNKNOWN_PROB for _ in range(config.BOARD_SIZE)] for _ in range(config.BOARD_SIZE)]
    
    def set_predictions(self, x, y, value):
        self.predictions[y][x] = value

    def pixel_to_grid(self, mouse_pos):
        mx, my = mouse_pos
        bx = self.renderer.board_x
        by = self.renderer.board_y
        return int((mx - bx) // config.CELL_WIDTH), int((my - by) // config.CELL_HEIGHT)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.renderer.reset_rect.collidepoint(event.pos):
                        self.board.reset()
                        self.reset_predictions()
                    elif self.renderer.ai_solve_rect.collidepoint(event.pos):
                        pass
                    elif self.renderer.ai_pred_rect.collidepoint(event.pos):
                        if self.click_mode != config.CLICK_AI_PRED:
                            print("AI-Predict-Mode activated")
                            self.click_mode = config.CLICK_AI_PRED
                        elif self.click_mode == config.CLICK_AI_PRED:
                            self.click_mode = config.CLICK_NORMAL
                    elif self.renderer.quit_rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
                    else:
                        x, y = self.pixel_to_grid(event.pos)
                        if 0 <= x < config.BOARD_SIZE and 0 <= y < config.BOARD_SIZE:
                            if self.click_mode == config.CLICK_NORMAL:
                                if event.button == config.REVEAL_BUTTON:
                                    _, died = self.board.reveal(x, y)
                                    self.reset_predictions()
                                    if died: print(stringify_board(self.board.hidden_board))
                                elif event.button == config.FLAG_BUTTON:
                                    self.board.flag(x, y)
                            elif self.click_mode == config.CLICK_AI_PRED:
                                prediction = self.ai.test(self.board, (x, y))
                                self.set_predictions(x, y, round(prediction[:,1][0] * 100, 2))
                                self.click_mode = config.CLICK_NORMAL
            self.screen.fill((0, 0, 0))
            self.renderer.draw_board(self.screen, self.board.hidden_board)
            self.renderer.draw_predictions(self.screen, self.predictions)
            self.renderer.draw_menu(self.screen)
            self.renderer.draw_cursor(self.click_mode, self.screen, pygame.mouse.get_pos())
            pygame.display.flip()
            self.clock.tick(config.FPS)

if __name__ == "__main__":
    game = Game()
    game.run()