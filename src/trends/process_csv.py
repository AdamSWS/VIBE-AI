import csv
import os
import time
import json
from scraper import start_scraping_session
from db import get_db, store_items_to_collection

# File to persist the processed topics index
INDEX_FILE = "./src/trends/processed_topics_index.json"

def load_processed_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as file:
            return json.load(file)
    return {"last_index": 0}

def save_processed_index(index):
    with open(INDEX_FILE, "w") as file:
        json.dump({"last_index": index}, file)

def reset_processed_index():
    save_processed_index(0)
    print("[INFO] Processed index has been reset to the start.")

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

def process_csv_topics(csv_file, batch_size=5, threads=7):
    topics = extract_trends_from_csv(csv_file)
    processed_index = load_processed_index().get("last_index", 0)

    if processed_index >= len(topics):
        print("[INFO] All topics in the CSV file have already been processed.")
        return

    while processed_index < len(topics):
        # Get the next batch of topics
        topics_to_process = topics[processed_index:processed_index + batch_size]
        print(f"[INFO] Processing topics: {topics_to_process}")

        # Perform scraping for the batch
        results = start_scraping_session(threads=threads, topics=topics_to_process)

        # Store the results and disconnect from the database
        if results:
            collection, client = get_db("trending_video_data")
            try:
                store_items_to_collection(collection, results)
                print(f"[INFO] Stored {len(results)} items in the database.")
            finally:
                client.close()

        # Update and save the processed index
        processed_index += len(topics_to_process)
        save_processed_index(processed_index)

        # Wait before the next batch (in loop mode)
        print("[INFO] Batch processing complete.")

    print("[INFO] Completed processing all topics in the CSV file.")

def process_csv_in_loop(csv_file, batch_size=5, interval=60, threads=7):
    print(f"[INFO] Starting loop mode for processing CSV topics. Interval: {interval} seconds.")
    try:
        while True:
            print("[INFO] Fetching the next batch of topics...")
            results = process_csv_topics(csv_file, batch_size=batch_size, threads=threads)  # Pass thread count

            if not results:
                print("[INFO] All topics in the CSV file have been processed. Exiting loop mode.")
                break

            print(f"[INFO] Sleeping for {interval} seconds before the next batch...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[INFO] Loop mode terminated by user.")

if __name__ == "__main__":
    user_file_path = input("[INPUT] Enter the path to the CSV file (leave blank to use default): ").strip()
    file_path = user_file_path if user_file_path else None
    trends = extract_trends_from_csv(file_path)
    print("[INFO] Extracted Trends:")
    for trend in trends:
        print(trend)
