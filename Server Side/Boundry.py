
from os import getuid

class Checkpoint():
    def __init__(self, type : str, num : int, total_checkpoints: int):
        self.type = type
        self.num = num
        self.total_checkpoints = total_checkpoints

class Map():
    def __init__(self):
        pass
