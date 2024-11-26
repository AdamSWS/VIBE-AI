import time
import os
import json
from vpn import connect_to_vpn, disconnect_vpn
from video_scraper import scrape_trending_videos
from db import get_db, store_items_to_collection
from trends import get_randomized_youtube_trending_topics, extract_trends_from_csv

# File to persist the processed topics index
INDEX_FILE = "processed_topics_index.json"

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

def start_scraping_session(threads=7, topics=None):
    if threads:
        print(f"[INFO] Starting scraping session with {threads} thread(s)...")
    else:
        print("[INFO] Starting scraping session without multithreading...")

    if not topics:
        print("[INFO] No topics provided. Fetching trending topics...")
        topics = get_randomized_youtube_trending_topics()

    print(f"[INFO] Fetched Topics: {topics}")

    all_results = []
    connect_to_vpn()

    for topic in topics:
        print(f"[INFO] Scraping videos for topic: {topic}")
        try:
            topic_results = scrape_trending_videos(topic, threads)
            all_results.extend(topic_results)
        except Exception as e:
            print(f"[ERROR] Failed to scrape videos for topic '{topic}': {e}")

    disconnect_vpn()

    if all_results:
        try:
            collection = get_db("trending_video_data")
            store_items_to_collection(collection, all_results)
            print(f"[INFO] Scraped data successfully stored in MongoDB. Total videos: {len(all_results)}")
        except Exception as e:
            print(f"[ERROR] Failed to store data in MongoDB: {e}")
    else:
        print("[WARNING] No results to store.")

    return all_results


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

def display_menu():
    """Display the interactive menu."""
    print("\n[INFO] YouTube Scraper Menu")
    print("1. Start scraping session")
    print("2. Connect to VPN (Mac Only)")
    print("3. Disconnect from VPN (Mac Only)")
    print("4. Process topics from CSV")
    print("5. Reset processed index")
    print("6. Exit")
    print()


def main():
    while True:
        display_menu()
        choice = input("[INPUT] Enter your choice: ")

        if choice == "1":
            print("[INFO] Do you want to enable multithreading for the scraping session?")
            threading_choice = input("[INPUT] Enter 'yes' to enable, or 'no' to disable: ").strip().lower()

            if threading_choice == "yes":
                while True:
                    num_threads_input = input("[INPUT] Enter the number of threads to use: ").strip()
                    if num_threads_input.isdigit() and int(num_threads_input) > 0:
                        num_threads = int(num_threads_input)
                        break
                    else:
                        print("[ERROR] Please enter a valid number greater than 0.")
            else:
                num_threads = None

            print("[INFO] Starting Single Mode...")
            topics = get_randomized_youtube_trending_topics()
            print(f"[INFO] Topics to scrape: {topics}")
            trending_video_stats = start_scraping_session(threads=num_threads, topics=topics)

            if trending_video_stats:
                print("[INFO] Scraped Video Details:")
                for video in trending_video_stats:
                    print(video)

        elif choice == "2":
            print("[INFO] Connecting to VPN (Mac Only)...")
            try:
                connect_to_vpn()
            except Exception as e:
                print(f"[ERROR] Failed to connect to VPN: {e}")

        elif choice == "3":
            print("[INFO] Disconnecting from VPN (Mac Only)...")
            try:
                disconnect_vpn()
            except Exception as e:
                print(f"[ERROR] Failed to disconnect from VPN: {e}")

        elif choice == "4":
            csv_file = input("[INPUT] Enter the path to the CSV file: ").strip()
            batch_size = int(input("[INPUT] Enter the number of topics to process at a time: ").strip())
            print("[INFO] Do you want to enable loop mode?")
            loop_mode = input("[INPUT] Enter 'yes' to enable, or 'no' to disable: ").strip().lower()
            interval = int(input("[INPUT] Enter the interval (in seconds) between batches: ").strip())
            process_csv_in_loop(csv_file, batch_size=batch_size, interval=interval)

        elif choice == "5":
            print("[INFO] Exiting the program. Goodbye!")
            break

        else:
            print("[ERROR] Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
