"""
Copyright (c) 2021 Philipp Scheer
"""


import requests


def store(url, path):
    r = requests.get(url)
    size = len(r.content)
    with open(path, 'wb') as f:
        f.write(r.content)
    return size
