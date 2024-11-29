from vpn import connect_to_vpn, disconnect_vpn
from trends import get_randomized_youtube_trending_topics, process_csv_in_loop, process_csv_in_loop_for_comments
from scraper import start_scraping_session, start_comment_scrape_session

def display_menu():
    """Display the interactive menu."""
    print("\n[INFO] YouTube Scraper Menu")
    print("1. Start scraping session")
    print("2. Connect to VPN (Mac Only)")
    print("3. Disconnect from VPN (Mac Only)")
    print("4. Process topics from CSV")
    print("5. Start comment scraping session")
    print("6. Reset processed index")
    print("7. Exit")
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
            # loop_mode = input("[INPUT] Enter 'yes' to enable, or 'no' to disable: ").strip().lower()
            interval = int(input("[INPUT] Enter the interval (in seconds) between batches: ").strip())
            process_csv_in_loop(csv_file, batch_size=batch_size, interval=interval)

        elif choice == "5":
            csv_file = input("[INPUT] Enter the path to the CSV file: ").strip()
            batch_size = int(input("[INPUT] Enter the number of topics to process at a time: ").strip())
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
            interval = int(input("[INPUT] Enter the interval (in seconds) between batches: ").strip())
            process_csv_in_loop_for_comments(csv_file, batch_size=batch_size, interval=interval)
            # print("[INFO] Starting Single Mode...")
            # topics = get_randomized_youtube_trending_topics()
            # print(f"[INFO] Topics to scrape: {topics}")
            # trending_video_stats = start_comment_scrape_session(threads=num_threads, topics=topics)

            if trending_video_stats:
                print("[INFO] Scraped Video Details:")
                for video in trending_video_stats:
                    print(video)


        elif choice == "6":
            print("[INFO] Exiting the program. Goodbye!")
            break

        else:
            print("[ERROR] Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
