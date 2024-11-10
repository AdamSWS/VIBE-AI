import os

def load_keywords(filepath='./data/keywords.txt'):
    filepath = os.path.join(os.path.dirname(__file__), filepath)
    with open(filepath, 'r') as file:
        keywords = [line.strip().lower() for line in file]
    return keywords
