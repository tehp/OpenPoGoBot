import os
import json

try:
    with open(os.path.join('config', 'plugins', 'transfer_pokemon.json'), 'r') as f:
        release_rules = json.load(f)
except IOError:
    release_rules = dict()
