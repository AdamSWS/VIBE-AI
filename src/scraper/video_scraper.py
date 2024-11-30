from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from db.db import get_db, store_items_to_collection
from .driver import create_driver
from queue import Queue
from threading import Lock
from .stats_parser import parse_likes, parse_view_count
from vpn.vpn_handler import connect_to_vpn, disconnect_vpn

MAX_VIDEOS = 50


def scrape_video_details(video_url):
    """Scrape detailed information for a given video URL."""
    print(f"[INFO] Scraping video details for: {video_url}")

    driver = create_driver()
    if not driver:
        print(f"[ERROR] Failed to create WebDriver for: {video_url}")
        return None

    try:
        driver.get(video_url)

        # Wait for the video page to load
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, '//h1[@class="style-scope ytd-watch-metadata"]/yt-formatted-string'))
        )

        # Scrape title
        try:
            title = driver.find_element(By.XPATH, '//h1[@class="style-scope ytd-watch-metadata"]/yt-formatted-string').text
        except Exception:
            title = "No title available"

        # Scrape description
        try:
            description = driver.find_element(By.XPATH, '//yt-attributed-string[@id="attributed-snippet-text"]').text
        except Exception:
            try:
                description = driver.find_element(By.XPATH, '//span[@id="plain-snippet-text"]').text
            except Exception:
                description = "No description available"

        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-button[@id='expand']"))).click()
        except Exception as e:
            print(f"[ERROR] Could not click 'More' button: {e}")

        # Scrape tags
        try:
            tags = driver.execute_script(
                "return document.querySelector('meta[name=\"keywords\"]').getAttribute('content');"
            )
            tags = tags.split(",") if tags else []
        except Exception:
            tags = []

        # Scrape upload date
        try:
            upload_date = driver.find_element(By.XPATH, '//span[@class="style-scope yt-formatted-string bold"][3]').text
        except Exception:
            upload_date = "Unknown"

        # Scrape view count
        try:
            view_count = driver.find_element(By.XPATH, '//span[@class="style-scope yt-formatted-string bold"][1]').text
        except Exception as e:
            print(f"[ERROR] Failed to fetch view count: {e}")
            view_count = "Unknown"

        # Scrape likes
        try:
            likes = driver.find_element(By.XPATH, '//*[@id="top-level-buttons-computed"]/segmented-like-dislike-button-view-model/yt-smartimation/div/div/like-button-view-model/toggle-button-view-model/button-view-model/button/div[2]').text
        except Exception:
            likes = "Unknown"

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "upload_date": upload_date,
            "view_count": parse_view_count(view_count),
            "likes": parse_likes(likes)
        }
    except Exception as e:
        print(f"[ERROR] Failed to scrape video details: {e}")
        return None
    finally:
        driver.quit()


def scrape_videos_for_topic(topic):
    """Scrape video URLs for a single topic."""
    print(f"[INFO] Scraping video URLs for topic: {topic}")
    driver = create_driver()

    if not driver:
        print("[ERROR] WebDriver could not be created. Exiting.")
        return []

    try:
        search_url = f"https://www.youtube.com/results?search_query={'+'.join(topic.split())}"
        driver.get(search_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//ytd-video-renderer'))
        )

        videos = driver.find_elements(By.XPATH, '//ytd-video-renderer')[:MAX_VIDEOS]
        video_urls = []
        for video in videos:
            try:
                video_url = video.find_element(By.XPATH, './/a[@id="video-title"]').get_attribute("href")
                if video_url and "/shorts/" not in video_url:
                    video_urls.append(video_url)
            except Exception as e:
                print(f"[ERROR] Failed to extract video URL: {e}")

        print(f"[INFO] Found {len(video_urls)} videos for topic: {topic}")
        return video_urls

    except Exception as e:
        print(f"[ERROR] Failed to scrape video URLs for topic '{topic}': {e}")
        return []
    finally:
        driver.quit()


def worker(queue, results, lock):
    """Worker function to scrape video details."""
    while not queue.empty():
        video_url = queue.get()
        if video_url is None:
            break

        video_data = scrape_video_details(video_url)
        if video_data:
            with lock:
                results.append(video_data)

        queue.task_done()


def start_scraping_session(topics, thread_count=20):
    """Scrape videos for all topics and process them concurrently."""
    print("[INFO] Starting scraping session...")
    connect_to_vpn()

    # Step 1: Scrape video URLs for all topics concurrently
    all_video_urls = []
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        topic_futures = {executor.submit(scrape_videos_for_topic, topic): topic for topic in topics}

        for future in topic_futures:
            try:
                urls = future.result()
                all_video_urls.extend(urls)
            except Exception as e:
                print(f"[ERROR] Error while scraping topic: {topic_futures[future]} - {e}")

    print(f"[INFO] Total video URLs scraped: {len(all_video_urls)}")

    # Step 2: Process video URLs concurrently
    video_queue = Queue()
    results = []
    lock = Lock()

    for url in all_video_urls:
        video_queue.put(url)

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for _ in range(thread_count):
            executor.submit(worker, video_queue, results, lock)

    video_queue.join()
    disconnect_vpn()

    # Step 3: Save results to the database
    try:
        collection = get_db("trending_video_data")
        store_items_to_collection(collection, results)
        print(f"[INFO] Stored {len(results)} videos in the database.")
    except Exception as e:
        print(f"[ERROR] Failed to store data in the database: {e}")

    return results


if __name__ == "__main__":
    topics = [
        'How to Convert PDF to Word #shorts',
        'Three EASY Ways to Find and Remove Duplicates in Excel',
        'How to Get a UNIQUE List from Many Columns Using FLATTEN in Google Sheets',
        'Microsoft Office Gets a NEW LOOK #shorts',
        'How to Use Excel Checkboxes | Interactive Checklists & Reports',
        '10 USEFUL Websites You Wish You Knew Earlier!',
        'Get Windows 11! How to Download & Install + Compatibility Check #shorts',
        'How to ACE Excel Interview Questions (Based on YOUR feedback & by Position)',
        "Top Features of EDGE! (You've GOT to KNOW these!)",
        'How to Translate Languages With Google Sheets #shorts'
    ]
    start_scraping_session(topics, thread_count=20)
