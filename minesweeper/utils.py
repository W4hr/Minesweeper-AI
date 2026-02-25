from typing import List

def bordered(text):
    """
    Surrounds text with a box
    
    :param text: the Minesweeper board to be surrounded
    """
    lines = text.splitlines()
    width = max(len(s) for s in lines)
    res = ['┌' + '─' * (width+2) + '┐']
    for s in lines:
        res.append('│ ' + s.ljust(width) + ' │')
    res.append('└' + '─' * (width+2) + '┘')
    return '\n'.join(res)

def stringify_board(self, board: List[List[int]], bomb = None):
    joined_board = ""
    if bomb is None:
        bomb = self.BOMB
    for i in board:
        joined_board += " ".join([str(j) if j != bomb else "*" for j in i]) + "\n"
    return bordered(joined_board)