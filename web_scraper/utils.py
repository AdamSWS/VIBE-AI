def load_keywords(filepath='./data/keywords.txt'):
    # Open the file in read mode
    with open(filepath, 'r') as file:
        # Read each line, strip whitespace, convert to lowercase, and store in a list
        keywords = [line.strip().lower() for line in file]
    return keywords