from base.py import Challenge
class Trivia(Challenge):

    """
    config.json inside server/ holds any information you want to hardcode into game
    like:

    {"question": "what 1+1 man", "answer": "2"}

    http server passes that dictonary into 
    """
    def __init__(self, config):
        self.config = config
        self.question = config["question"]


    # anything returned by tihs function will be included in response to frontend
    # like the quesiton bein asked!
    def start(self, token):
        # pls return as a dictionary
        return {"question": self.config["question"]}

    # returns if that answer was correct
    def submit(self, token, answer) -> bool:
        return self.config["answer"] == answer
