import csv
import os
import time
import json
from scraper import start_scraping_session, start_comment_scrape_session
from db import get_db, store_items_to_collection, save_comments_batch

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
        file_path = os.path.abspath("./src/trends/data/data_science_youtube_stats.csv")
    
    titles = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)  # Use DictReader for named columns
            for row in reader:
                if "Title" in row:
                    titles.append(row["Title"])  # Extract titles from "Trends" column
    except Exception as e:
        print(f"[ERROR] Failed to process the CSV file: {e}")
    return titles

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
        results = start_scraping_session(topics=topics_to_process, thread_count=12)

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

def process_csv_in_loop_for_comments(csv_file, batch_size=5, interval=60, threads=7):
    print(f"[INFO] Starting loop mode for processing CSV topics. Interval: {interval} seconds.")
    try:
        while True:
            print("[INFO] Fetching the next batch of topics...")
            results = process_csv_topics_for_comments(csv_file, batch_size=batch_size, threads=threads)  # Pass thread count

            if not results:
                print("[INFO] All topics in the CSV file have been processed. Exiting loop mode.")
                break

            print(f"[INFO] Sleeping for {interval} seconds before the next batch...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[INFO] Loop mode terminated by user.")

def process_csv_topics_for_comments(csv_file, batch_size=5, threads=7):
    """
    Process topics from a CSV file and scrape YouTube comments for each topic.
    """
    topics = extract_trends_from_csv(csv_file)
    processed_index = load_processed_index().get("last_index", 0)

    if processed_index >= len(topics):
        print("[INFO] All topics in the CSV file have already been processed.")
        return

    while processed_index < len(topics):
        # Get the next batch of topics
        topics_to_process = topics[processed_index:processed_index + batch_size]
        print(f"[INFO] Processing topics for comments: {topics_to_process}")

        # Perform comment scraping for the batch of topics
        results = start_comment_scrape_session(topics=topics_to_process, thread_count=threads)

        if not results:
            print(f"[WARNING] No comments scraped for topics: {topics_to_process}.")
            continue

        # Save comments grouped by video title
        for video_data in results:
            video_title = video_data.get("title", "Unknown Title")
            comments_batch = video_data.get("comments", [])
            if not comments_batch:
                print(f"[DEBUG] No comments to save for video '{video_title}'.")
                continue
            
            # Save to MongoDB using save_comments_batch
            save_comments_batch(comments_batch, video_title)

        # Update and save the processed index
        processed_index += len(topics_to_process)
        save_processed_index(processed_index)

        print("[INFO] Batch processing complete.")

    print("[INFO] Completed processing all topics in the CSV file.")

if __name__ == "__main__":
    user_file_path = input("[INPUT] Enter the path to the CSV file (leave blank to use default): ").strip()
    file_path = user_file_path if user_file_path else None
    trends = extract_trends_from_csv(file_path)
    print("[INFO] Extracted Trends:")
    for trend in trends:
        print(trend)
