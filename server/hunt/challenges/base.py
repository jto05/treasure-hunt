class Challenge:
    """
    PARENT CLASS!!!!

    everybody make their challenge a child of ts
    
    functions below MUST be implemented
    """

    def start(self, token):
        raise NotImplementedError

    def submit(self, token, answer):
        raise NotImplementedError

