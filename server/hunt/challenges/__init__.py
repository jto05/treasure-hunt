from .example_trivia import Trivia
from .memory_matrix import MemoryMatrix
from .timebank_trivia import TimebankTrivia


# registry of challenges
CHALLENGES = {
    "trivia": Trivia,
    "memory_matrix": MemoryMatrix,
    "timebank_trivia": TimebankTrivia,
}

# example json
# {"type": "trivia", "question": "1+1?", "answer": "2"}
#
def build(challenge_config, node=None, store=None):
    cfg = dict(challenge_config)
    # remove "type" from the config
    challenge_type = cfg.pop("type")

    # return the proper constructor for challenge type
    return CHALLENGES[challenge_type](cfg, node, store)
