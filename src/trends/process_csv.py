"""
This file extracts trending topics from a CSV file, defaulting to a predefined
file path if none is provided. It reads the CSV, processes the first column of
each row, and returns the extracted trends.
"""

import csv
import os

def extract_trends_from_csv(file_path=None):
    # Default file path if none is provided
    if not file_path:
        file_path = os.path.abspath("./src/trends/data/trending_US_7d_20241125-1756.csv")
    
    trends = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if row:
                    trends.append(row[0])
    except Exception as e:
        print(f"[ERROR] Failed to process the CSV file: {e}")
    return trends

if __name__ == "__main__":
    user_file_path = input("[INPUT] Enter the path to the CSV file (leave blank to use default): ").strip()
    file_path = user_file_path if user_file_path else None
    trends = extract_trends_from_csv(file_path)
    print("[INFO] Extracted Trends:")
    for trend in trends:
        print(trend)
