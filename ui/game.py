import pygame
import sys
from minesweeper.interactive import MinesweeperAPI

board_dimensions = 10
bomb_percentage = 15
board = MinesweeperAPI(board_dimensions, bomb_percentage, [[0,0]])
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

    COLOR_MAP = {
        1: (0, 255, 0),      # Pure Green
        2: (73, 255, 0),
        3: (146, 255, 0),
        4: (219, 255, 0),
        5: (255, 219, 0),
        6: (255, 146, 0),
        7: (255, 73, 0),
        8: (255, 0, 0)       # Pure Red
    }

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
    if isinstance(value, int) and value in config.COLOR_MAP: color = config.COLOR_MAP[value]
    else: color = (0, 0, 0)
    if value == config.BOMB:
        value = config.DISP_BOMB
    elif value == config.HIDDEN:
        return
    elif value == config.FLAG:
        value = config.DISP_FLAG
    
    text_surface = font.render(str(value), True, color)
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

class MenuConfig:
    width = 200
    height = 200

    retrybtn_size = (100, 40)

    def __init__(self):
        self.menu_pos = ((config.width-MenuConfig.width)/2, (config.height-MenuConfig.height)/2)
        self.retrybtn_pos = (self.menu_pos[0] + ((self.width - self.retrybtn_size[0])/2), self.menu_pos[1] + ((self.height - self.retrybtn_size[1])/2))

menuConfig = MenuConfig()

def draw_menu(surface, font = font):
    left = (config.width-MenuConfig.width)/2
    top = (config.height-MenuConfig.height)/2
    menu= pygame.Rect(left, top, MenuConfig.width, MenuConfig.height)
    pygame.draw.rect(surface, (180, 180, 180), menu)
    retry_btn = pygame.Rect(menuConfig.retrybtn_pos, menuConfig.retrybtn_size)
    pygame.draw.rect(surface, (180, 180, 180), retry_btn)
    pygame.draw.rect(surface, (0, 0, 0), retry_btn, 1)
    retry_text_surface = font.render("Retry", True, (0,0,0))
    retry_text_rect = retry_text_surface.get_rect(center=retry_btn.center)
    surface.blit(retry_text_surface, retry_text_rect)

moves = 0

game_over = False
has_won = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if not game_over and not has_won:
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pixel_to_grid(event.pos, config.grid_origin, config.cell_size)
                if event.button == 1:
                    if 0 <= x < board.size and 0 <= y < board.size:
                        if moves == 0:
                            board = MinesweeperAPI(board_dimensions, bomb_percentage, [(x,y), [0, 0]])
                        _, died = board.reveal(x, y)
                        moves += 1
                        game_over = died
                        has_won = board.has_won(died)
                elif event.button == 3:
                    board.flag(x, y)
        else:
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if menuConfig.retrybtn_pos[0] < x < menuConfig.retrybtn_pos[0] + menuConfig.retrybtn_size[0]:
                    print("reset")
                    board = MinesweeperAPI(board_dimensions, bomb_percentage)
                    has_won = False
                    game_over = False
                    moves = 0

    screen.fill((0,0,0))
    draw_board(screen, board)
    if game_over or has_won:
        draw_menu(screen)
    pygame.display.flip()
    clock.tick(60)