from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from db.db import get_db, store_items_to_collection, save_comments_batch
from scraper.driver import create_driver
from vpn.vpn_handler import connect_to_vpn, disconnect_vpn
from queue import Queue
from threading import Lock
import time
import random

MAX_COMMENTS = 400
MAX_VIDEOS = 20

def scrape_video_comments(video_url, video_title, max_comments=MAX_COMMENTS):
    """Scrape comments from a YouTube video."""
    driver = create_driver()
    if not driver:
        print(f"[ERROR] Failed to create WebDriver for: {video_url}")
        return {"title": video_title, "comments": []}

    try:
        driver.get(video_url)

        # Wait for the comment section to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="comments"]'))
        )

        # Scroll to the comments section to ensure it's in view
        comments_section = driver.find_element(By.XPATH, '//*[@id="comments"]')
        driver.execute_script("arguments[0].scrollIntoView();", comments_section)
        time.sleep(2)  # Allow the comments section to stabilize

        comments = []
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        retries = 0

        while len(comments) < max_comments and retries < 5:
            # Extract comments and their like counts
            comment_elems = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
            like_elems = driver.find_elements(By.XPATH, '//*[@id="vote-count-middle"]')

            for comment, like in zip(comment_elems, like_elems):
                comments.append({
                    "text": comment.text,
                    "likes": like.text if like.text else "0",
                })

                if len(comments) >= max_comments:
                    break

            # Stop scrolling if no new comments are loaded
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                retries += 1
            else:
                retries = 0  # Reset retries if new comments are loaded
            last_height = new_height

        return {"title": video_title, "comments": comments}

    except Exception as e:
        print(f"[ERROR] Failed to scrape comments for video '{video_url}': {e}")
        return {"title": video_title, "comments": []}
    finally:
        driver.quit()


def scrape_video_urls(topic):
    """Scrape video URLs and titles for a given topic."""
    driver = create_driver()
    if not driver:
        print("[ERROR] Failed to create WebDriver for scraping video URLs.")
        return []

    try:
        search_url = f"https://www.youtube.com/results?search_query={'+'.join(topic.split())}"
        driver.get(search_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//ytd-video-renderer'))
        )

        videos = driver.find_elements(By.XPATH, '//ytd-video-renderer')[:MAX_VIDEOS]
        video_data = []

        for video in videos:
            try:
                video_url = video.find_element(By.XPATH, './/a[@id="video-title"]').get_attribute("href")
                video_title = video.find_element(By.XPATH, './/a[@id="video-title"]').text.strip()
                if "/shorts/" not in video_url:
                    video_data.append({"url": video_url, "title": video_title})
            except Exception as e:
                print(f"[ERROR] Failed to extract video data: {e}")

        return video_data

    except Exception as e:
        print(f"[ERROR] Failed to scrape video URLs for topic '{topic}': {e}")
        return []
    finally:
        driver.quit()


def worker(queue, results, lock):
    """Worker function to scrape comments from a video."""
    while not queue.empty():
        video_data = queue.get()
        if video_data is None:
            break

        video_url = video_data["url"]
        video_title = video_data["title"]
        comments_data = scrape_video_comments(video_url, video_title)
        if comments_data:
            with lock:
                results.append(comments_data)

        queue.task_done()


def scrape_comments_for_topic(topic, thread_count=7):
    """Scrape comments for videos under a given topic."""
    print(f"[INFO] Starting scraping session for topic: {topic}")

    # Results container for the topic
    results = []

    try:
        # Connect to VPN
        print("[INFO] Connecting to VPN...")
        connect_to_vpn()

        # Fetch video URLs and titles
        video_data_list = scrape_video_urls(topic)
        if not video_data_list:
            print(f"[WARNING] No video URLs found for topic '{topic}'.")
            return []

        print(f"[INFO] Found {len(video_data_list)} videos for topic '{topic}'.")

        # Prepare threading components
        video_queue = Queue()
        lock = Lock()

        # Add video data to the queue
        for video_data in video_data_list:
            video_queue.put(video_data)

        print(f"[INFO] Queue initialized with {len(video_data_list)} videos.")

        # Multithreaded comment scraping
        print(f"[INFO] Starting comment scraping with {thread_count} threads.")
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            for _ in range(thread_count):
                executor.submit(worker, video_queue, results, lock)

        # Wait for all tasks to complete
        video_queue.join()

        print(f"[INFO] Completed scraping comments for topic '{topic}'. Videos processed: {len(results)}")
        return results

    except Exception as e:
        print(f"[ERROR] Failed to scrape comments for topic '{topic}': {e}")
        return []
    finally:
        disconnect_vpn()


def start_comment_scrape_session(topics, thread_count=7):
    """Start a session to scrape comments for videos based on provided topics."""
    print(f"[INFO] Starting comment scraping session for {len(topics)} topics with {thread_count} threads per topic.")

    all_results = []

    for topic in topics:
        print(f"[INFO] Processing topic: {topic}")
        try:
            topic_results = scrape_comments_for_topic(topic, thread_count=thread_count)
            all_results.extend(topic_results)
        except Exception as e:
            print(f"[ERROR] Failed to scrape comments for topic '{topic}': {e}")

    # Store results in MongoDB
    print("[INFO] Storing scraped comments in database...")
    try:
        for result in all_results:
            save_comments_batch(result["comments"], result["title"])
        print("[INFO] Successfully stored comments in MongoDB.")
    except Exception as e:
        print(f"[ERROR] Failed to store comments in database: {e}")

    print("[INFO] Comment scraping session completed. Total topics processed: ", len(topics))


if __name__ == "__main__":
    topics = ["Minimalist Art", "Independent Films", "Urban Street Art"]
    start_comment_scrape_session(topics, thread_count=7)
