from .example_trivia import Trivia


# registry of challenges
CHALLENGES = {"trivia" : Trivia}

# example json
# {"type": "trivia", "question": "1+1?", "answer": "2"}
#
def build(challenge_config):
    cfg = dict(challenge_config)
    # remove "type" from the config
    challenge_type = cfg.pop("type")

    # return the proper constructor for challenge type
    return CHALLENGES[challenge_type](cfg)
