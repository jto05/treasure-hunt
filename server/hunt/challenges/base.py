from ..state import GameStore

class Challenge:
    """
    PARENT CLASS!!!!

    everybody make their challenge a child of ts

    functions below MUST be implemented
    """

    def __init__(self, config: dict, node, store: GameStore):
        self.config = config
        self.node = node
        self.store = store

    def start(self, token) -> dict:
        raise NotImplementedError

    def submit(self, token, answer) -> dict:
        raise NotImplementedError

