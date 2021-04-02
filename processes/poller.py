"""
Copyright (c) 2021 Philipp Scheer
"""


import requests
from packaging import version

def poll(version_url, version_local):
    remote_version = requests.get(version_url).text.strip()
    with open(version_local, "r") as f:
        local_version = f.read().strip()
    return (version.parse(remote_version), version.parse(local_version))
