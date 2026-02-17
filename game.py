import pygame
import sys
from interactive import MinesweeperAPI

board_dimensions = 10
board = MinesweeperAPI(board_dimensions)
board.set_hidden_board()

class Config:
    dynamic = True

    width = 800
    height = 800

    board_dimensions = board_dimensions
    cell_size = 40
    
    HIDDEN = board.HIDDEN
    BOMB = board.BOMB
    FLAG = board.FLAG

    DISP_BOMB = "*"
    DISP_FLAG = "🏴‍☠️"

    def __init__(self):
        if (self.dynamic):
            self.cell_size = min(self.height, self.width)/board_dimensions
        self.grid_origin = (
            (self.width - board.size * self.cell_size) // 2,
            (self.height - board.size * self.cell_size) // 2
        )

config = Config()

pygame.init()
screen = pygame.display.set_mode(size=(config.width,config.height))
pygame.display.set_caption("Minesweeper")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 50)

def pixel_to_grid(mouse_pos, grid_origin, cell_size):
    mx, my = mouse_pos
    gx, gy = grid_origin
    return int((mx - gx)//cell_size), int((my - gy)//cell_size)

def draw_cell(surface, rect, value, font = font):
    if value == 0:
        pygame.draw.rect(surface, (210, 210, 210), rect)
    else:
        pygame.draw.rect(surface, (180, 180, 180), rect)
    pygame.draw.rect(surface, (0, 0, 0), rect, 1) # Border
    if value == config.BOMB:
        value = config.DISP_BOMB
    elif value == config.HIDDEN:
        return
    elif value == config.FLAG:
        value = config.DISP_FLAG
    text_surface = font.render(str(value), True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

def draw_board(surface, board):
    for y in range(board.size):
        for x in range(board.size):
            origin_x, origin_y = config.grid_origin

            left = origin_x + x * config.cell_size
            top  = origin_y + y * config.cell_size

            button_rect = pygame.Rect(left, top, config.cell_size, config.cell_size)
            draw_cell(surface, button_rect, board.get_cell(x, y))

moves = 0

game_over = False
while not game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pixel_to_grid(event.pos, config.grid_origin, config.cell_size)
            if event.button == 1:
                if 0 <= x < board.size and 0 <= y < board.size:
                    if moves == 0:
                        board = MinesweeperAPI(board_dimensions, [(x,y)])
                    _, died = board.reveal(x, y)
                    moves += 1
                    if died: game_over = True
            elif event.button == 3:
                board.flag(x, y)
    screen.fill((0,0,0))
    draw_board(screen, board)
    pygame.display.flip()
    clock.tick(60)