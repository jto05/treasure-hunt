from .base import Challenge
class Trivia(Challenge):

    """
    config.json inside server/ holds any information you want to hardcode into game
    like:

    {"type" : "trivia", "question": "what 1+1 man", "answer": "2"}
        ^ this field is necessary to include in config.json and gets popped off when built

    {"question": "what 1+1 man", "answer": "2"}
    this is an example of what is passed into constructor

    http server passes that dictonary into 
    """
    def __init__(self, config):
        self.config = config
        self.question = config["question"]


    """
    anything returned by tihs function will be included in response to frontend
    like the quesiton bein asked!

    'token' can be used to track attempts made by teams, or track saved states 
    of each team
    """
    
    def start(self, token) -> dict:
        # pls return as a dictionary
        return {"question": self.config["question"]}

    # returns if that answer was correct
    def submit(self, token, answer) -> dict:
        # return as a dict b/c everything routed through http server is JSON
        correct = self.config["answer"] == answer
        return {"correct": correct}
