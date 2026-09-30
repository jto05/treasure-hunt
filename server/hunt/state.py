import secrets

class GameStore():
    def __init__(self):
        # key is the token generated and the value is the mac
        # address 
        self._teams = {} 
    def register_team(self, name, mac):
        token = secrets.token_hex(16) # generates a token that acts like a key for the team
        self._teams[token] = {
            "name": name,
            "mac":  mac.lower() if mac else None,
        }

        return token


