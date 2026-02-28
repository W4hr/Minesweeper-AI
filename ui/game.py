import pygame
from ui.config import config
import sys
import time
from ui.renderer import Renderer
from minesweeper.interactive import MinesweeperAPI
from minesweeper.utils import round_prediction
from minesweeper.stats import stats

from minesweeper.utils import stringify_board

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("MinesweeperAI")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer()
        self.board = MinesweeperAPI()
        self.click_mode = config.CLICK_NORMAL
        self.reset_predictions()
        self.ai_revealed = []
        self.ai_solving = False
        self.algo_revealed = []
        self.dual_solving = False
        self.last_ai_move = 0

    def reset_predictions(self):
        self.predictions = [[config.UNKNOWN_PROB for _ in range(config.BOARD_SIZE)] for _ in range(config.BOARD_SIZE)]
    
    def reset(self):
        self.board.reset()
        self.reset_predictions()
        self.ai_revealed = []
        self.algo_revealed = []

    def set_predictions(self, x, y, value):
        self.predictions[y][x] = value

    def pixel_to_grid(self, mouse_pos):
        mx, my = mouse_pos
        bx = self.renderer.board_x
        by = self.renderer.board_y
        return int((mx - bx) // config.CELL_WIDTH), int((my - by) // config.CELL_HEIGHT)

    def filtered_predictions(self):
        return [
                [
                    self.predictions[y][x] if self.board.hidden_board[y][x] == -1 else config.UNKNOWN_PROB
                    for x in range(config.BOARD_SIZE)
                ]
                for y in range(config.BOARD_SIZE)
            ]
    
    def disable_others(self):
        self.ai_solving = False
        self.dual_solving = False
        self.click_mode = config.CLICK_NORMAL

    def quit(self):
        stats.save()
        pygame.quit()
        sys.exit()
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.renderer.reset_rect.collidepoint(event.pos):
                        self.reset()
                    elif self.renderer.ai_solve_rect.collidepoint(event.pos):
                        if self.ai_solving:
                            self.disable_others()
                        else:
                            self.disable_others()
                            self.ai_solving = True
                            self.click_mode = config.CLICK_FORBIDDEN
                    elif self.renderer.ai_pred_rect.collidepoint(event.pos):
                        if self.click_mode != config.CLICK_AI_PRED:
                            self.disable_others()
                            print("AI-Predict-Mode activated")
                            self.click_mode = config.CLICK_AI_PRED
                        else:
                            self.click_mode = config.CLICK_NORMAL
                    elif self.renderer.auto_pred_rect.collidepoint(event.pos):
                        self.predictions = self.board.predict_all()
                    elif self.renderer.ai_move_rect.collidepoint(event.pos):
                        picked_coordinates = self.board.ai_move()
                        if picked_coordinates:
                            self.ai_revealed.append(picked_coordinates)
                        self.reset_predictions()
                    elif self.renderer.algo_move_rect.collidepoint(event.pos):
                        if self.click_mode != config.CLICK_ALGO_PRED:
                            self.disable_others()
                            self.click_mode = config.CLICK_ALGO_PRED
                        else:
                            self.click_mode = config.CLICK_NORMAL
                    elif self.renderer.algo_solve_rect.collidepoint(event.pos):
                        self.board.auto_algo(self.algo_revealed)
                        self.reset_predictions()
                    elif self.renderer.dual_solve_rect.collidepoint(event.pos):
                        if self.dual_solving:
                            self.disable_others()
                        else:
                            self.disable_others()
                            self.dual_solving = True
                            self.click_mode = config.CLICK_FORBIDDEN
                    elif self.renderer.quit_rect.collidepoint(event.pos):
                        self.quit()
                    else:
                        x, y = self.pixel_to_grid(event.pos)
                        if 0 <= x < config.BOARD_SIZE and 0 <= y < config.BOARD_SIZE:
                            if self.click_mode == config.CLICK_NORMAL:
                                if event.button == config.REVEAL_BUTTON and not self.board.ended() and not self.ai_solving:
                                    _, died = self.board.reveal(x, y)
                                    self.reset_predictions()
                                    if died: 
                                        print(stringify_board(self.board.hidden_board))
                                        self.renderer.draw_revealed(self.screen, self.ai_revealed, self.algo_revealed)
                                elif event.button == config.FLAG_BUTTON:
                                    self.board.flag(x, y)
                                    self.reset_predictions()
                            elif self.click_mode == config.CLICK_AI_PRED:
                                prediction = round_prediction(self.board.predict((x, y)))
                                self.set_predictions(x, y, prediction)
                            elif self.click_mode == config.CLICK_ALGO_PRED:
                                self.board.algo_move((x, y), self.algo_revealed)
                                self.reset_predictions()
            if self.ai_solving or self.dual_solving:
                current_time = time.time()
                if current_time - self.last_ai_move > config.DELAY_AI_SOLVE / 1000:
                    if not self.board.ended():
                        if self.ai_solving:
                            picked_coordinates = self.board.ai_move()
                            if picked_coordinates:
                                self.ai_revealed.append(picked_coordinates)
                        if self.dual_solving:
                            picked_coordinates = self.board.ai_move()
                            if picked_coordinates:
                                self.ai_revealed.append(picked_coordinates)
                            self.board.auto_algo(self.algo_revealed)
                        self.last_ai_move = current_time
                        self.reset_predictions()
                    else:
                        self.reset()
            self.screen.fill((0, 0, 0))
            self.renderer.draw_board(self.screen, self.board.hidden_board)
            self.renderer.draw_predictions(self.screen, self.filtered_predictions())
            self.renderer.draw_revealed(self.screen, self.ai_revealed, self.algo_revealed)
            self.renderer.draw_menu(self.screen, self.board.has_won(), self.board.has_died, self.board.bomb_count - self.board.get_flag_count(), self.ai_solving or self.dual_solving, len(stats))
            self.renderer.draw_cursor(self.click_mode, self.screen, pygame.mouse.get_pos())

            pygame.display.flip()
            self.clock.tick(config.FPS)

if __name__ == "__main__":
    game = Game()
    game.run()