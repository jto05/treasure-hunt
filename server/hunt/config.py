import json

def load_config(path="config.json"):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return "no config found"




