import csv
import numpy as np
import pandas
from minesweeper.config import config

class Stats:
    def __init__(self):
        self.record = []
    def log(self, has_won, has_died, moves, bomb_count, dimensions, cells_revealed):
        data = {
            "has_won": has_won, 
            "has_died": has_died,
            "moves": moves,
            "bomb_count": bomb_count,
            "dimensions": dimensions,
            "cells_revealed": cells_revealed,
            "number_cells_left": dimensions ** 2 - cells_revealed - bomb_count
        }
        self.record.append(data)

    def save(self):
        if not self.record:
            return
        keys = self.record[0].keys()
        with open(config.CSV_NAME, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.record)

    def has_record(self):
        return len(self.record) > 0

    def get_average_moves(self):
        if self.has_record():
            moves = [r["moves"] for r in self.record]
            return np.average(moves)
        else:
            try:
                df = pandas.read_csv(config.CSV_NAME)
                return np.average(df["moves"])
            except FileNotFoundError:
                return 0
        
    def __len__(self):
        if self.has_record():
            return len(self.record)
        else:
            try:
                df = pandas.read_csv(config.CSV_NAME)
                return len(df)
            except FileNotFoundError:
                return 0

stats = Stats()

if __name__ == "__main__":
    print(f"Average Moves: {stats.get_average_moves()}")
    print(f"Games: {len(stats)}")