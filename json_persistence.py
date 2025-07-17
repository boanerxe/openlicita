# coding=utf-8

import json

def store_json(file, symbol):
        """
        Save listing into local json file
        """
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(symbol, f, indent=4, ensure_ascii=False)

def load_json(file):
    """
    Update Json file
    """
    with open(file, "r+", encoding='utf-8') as f:
        return json.load(f)