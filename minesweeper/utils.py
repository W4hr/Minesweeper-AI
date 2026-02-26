from typing import List
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

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

def stringify_board(board: List[List[int]], bomb = None):
    joined_board = ""
    for i in board:
        joined_board += " ".join([str(j) if j != bomb else "*" for j in i]) + "\n"
    return bordered(joined_board)

def round_prediction(prediction):
    return round(prediction * 100, 2)

def probability_to_color(value):
    normColor = mcolors.Normalize(vmin=0, vmax=100)
    cmap = plt.get_cmap('RdYlGn_r')
    rgba = cmap(normColor(value))
    return (int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255))