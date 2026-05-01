import csv
import numpy as np
import pandas
from pandas.errors import EmptyDataError
from minesweeper.config import config
import os
import json
from datetime import datetime
from glob import glob
from enum import Enum

class Stats:
    """Class to log and manage game and AI training statistics."""
    SESSION_FIELDNAMES = [
        "session_id",
        "timestamp",
        "event",
        "config",
        "data_generation_seconds",
        "model_training_seconds",
        "trainingsdata_amount",
        "radius",
        "bomb_percentage",
        "include_bomb_count",
        "include_hidden_count",
        "include_revealed_count",
    ]

    def __init__(self):
        self.record: list = []
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.session_csv_name: str = self._derive_csv_name("_session")
        self.archive_dir: str = self._derive_archive_dir()
        self._archive_previous_game_csv()
        self._log_startup_context()

    def _split_csv_name(self):
        base, ext = os.path.splitext(config.CSV_NAME)
        if not ext:
            ext = ".csv"
        return base, ext

    def _derive_csv_name(self, suffix):
        base, ext = self._split_csv_name()
        return f"{base}{suffix}{ext}"

    def _derive_archive_dir(self):
        csv_dir = os.path.dirname(config.CSV_NAME)
        return os.path.join(csv_dir, "stats_archive") if csv_dir else "stats_archive"

    def _archive_previous_game_csv(self):
        if not os.path.exists(config.CSV_NAME):
            return

        os.makedirs(self.archive_dir, exist_ok=True)
        _, ext = self._split_csv_name()
        csv_basename = os.path.splitext(os.path.basename(config.CSV_NAME))[0]
        archive_name = f"{csv_basename}_{self.session_id}{ext}"
        archive_path = os.path.join(self.archive_dir, archive_name)
        os.replace(config.CSV_NAME, archive_path)

    def _config_snapshot(self):
        config_data = {}
        for key in dir(config):
            if key.isupper():
                value = getattr(config, key)
                if not callable(value):
                    config_data[key] = self._serialize_config_value(value)
        return json.dumps(config_data, sort_keys=True)

    def _serialize_config_value(self, value):
        if isinstance(value, Enum):
            return value.value
        return value

    def _append_session_row(self, row):
        file_exists = os.path.exists(self.session_csv_name)
        with open(self.session_csv_name, "a", newline="") as output_file:
            dict_writer = csv.DictWriter(
                output_file,
                fieldnames=self.SESSION_FIELDNAMES,
                extrasaction="ignore",
            )
            if not file_exists or os.path.getsize(self.session_csv_name) == 0:
                dict_writer.writeheader()
            dict_writer.writerow(row)

    def _base_session_row(self, event):
        return {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "config": "",
            "data_generation_seconds": "",
            "model_training_seconds": "",
            "trainingsdata_amount": "",
            "radius": "",
            "bomb_percentage": "",
            "include_bomb_count": "",
            "include_hidden_count": "",
            "include_revealed_count": "",
        }

    def _log_startup_context(self):
        row = self._base_session_row("startup")
        row["config"] = self._config_snapshot()
        self._append_session_row(row)

    def log_training(
        self,
        data_generation_seconds,
        model_training_seconds,
        trainingsdata_amount,
        radius,
        bomb_percentage,
        include_bomb_count,
        include_hidden_count,
        include_revealed_count,
    ):
        row = self._base_session_row("model_training")
        row["data_generation_seconds"] = data_generation_seconds
        row["model_training_seconds"] = model_training_seconds
        row["trainingsdata_amount"] = trainingsdata_amount
        row["radius"] = radius
        row["bomb_percentage"] = bomb_percentage
        row["include_bomb_count"] = include_bomb_count
        row["include_hidden_count"] = include_hidden_count
        row["include_revealed_count"] = include_revealed_count
        self._append_session_row(row)

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

    def _saved_game_csv_paths(self):
        paths = []
        if os.path.exists(config.CSV_NAME):
            paths.append(config.CSV_NAME)

        base_name = os.path.splitext(os.path.basename(config.CSV_NAME))[0]
        archive_pattern = os.path.join(self.archive_dir, f"{base_name}_*.csv")
        paths.extend(sorted(glob(archive_pattern)))
        return paths

    def _load_saved_game_dataframe(self):
        frames = []
        for csv_path in self._saved_game_csv_paths():
            try:
                df = pandas.read_csv(csv_path)
            except (FileNotFoundError, EmptyDataError):
                continue
            if "moves" in df.columns and "has_won" in df.columns:
                frames.append(df)

        if not frames:
            return None
        return pandas.concat(frames, ignore_index=True)

    def _load_current_session_game_dataframe(self):
        if not os.path.exists(config.CSV_NAME):
            return None
        try:
            df = pandas.read_csv(config.CSV_NAME)
            if "moves" in df.columns and "has_won" in df.columns:
                return df
        except (FileNotFoundError, EmptyDataError):
            pass
        return None

    def has_record(self):
        return len(self.record) > 0

    def get_average_moves(self, last_session_only=False):
        if self.has_record():
            moves = [r["moves"] for r in self.record]
            return np.average(moves)
        else:
            df = self._load_current_session_game_dataframe() if last_session_only else self._load_saved_game_dataframe()
            if df is None or df.empty:
                return 0
            return np.average(df["moves"])
        
    def __len__(self, saved=True, last_session_only=False):
        if self.has_record():
            return len(self.record)
        elif saved:
            df = self._load_current_session_game_dataframe() if last_session_only else self._load_saved_game_dataframe()
            if df is None:
                return 0
            return len(df)
        return 0
            
    def percentage_won(self, last_session_only=False):
        if self.has_record():
            won = [r["has_won"] for r in self.record]
        else:
            df = self._load_current_session_game_dataframe() if last_session_only else self._load_saved_game_dataframe()
            if df is None or df.empty:
                return 0
            won = df["has_won"]
        games_won = 0
        games_lost = 0
        for has_won in won:
            if has_won:
                games_won += 1
            else:
                games_lost += 1
        return round(games_won / (games_won + games_lost) * 100, 2)

    def remove_csv(self):
        os.remove(config.CSV_NAME)

stats = Stats()

if __name__ == "__main__":
    import sys
    last_session = "--last-session" in sys.argv
    print(f"Average Moves: {stats.get_average_moves(last_session_only=last_session)}")
    print(f"Games: {stats.__len__(last_session_only=last_session)}")
    print(f"Games won (%): {stats.percentage_won(last_session_only=last_session)}%")
    if last_session:
        print("(Data from last session only)")