import re


def extract_ids(L):
    ids = []
    for l in L:
        match = re.search(r"^\s*-?\s*id:\s*(\S+)", l)
        if match:
            ids.append(match.group(1))
    return ids
