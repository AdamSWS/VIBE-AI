from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from db.db import get_db, save_comments_batch
from scraper.driver import create_driver
from vpn.vpn_handler import connect_to_vpn, disconnect_vpn
from queue import Queue
from threading import Lock
import time

MAX_COMMENTS = 400
MAX_VIDEOS = 20


from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

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

        # Scroll to the comment section to ensure it's in view
        comments_section = driver.find_element(By.XPATH, '//*[@id="comments"]')
        driver.execute_script("arguments[0].scrollIntoView();", comments_section)

        comments = []
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        retries = 0

        while len(comments) < max_comments and retries < 5:
            # Extract visible comments
            comment_elems = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
            like_elems = driver.find_elements(By.XPATH, '//*[@id="vote-count-middle"]')

            for comment, like in zip(comment_elems, like_elems):
                comment_text = comment.text.strip()
                if not any(c['text'] == comment_text for c in comments):  # Avoid duplicates
                    comments.append({
                        "text": comment_text,
                        "likes": like.text.strip() if like.text.strip() else "0",
                    })

                if len(comments) >= max_comments:
                    break

            # Scroll down to load more comments
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)  # Allow time for new comments to load

            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                retries += 1  # Retry if the page height doesn't change
            else:
                retries = 0  # Reset retries if scrolling worked
            last_height = new_height

        return {"title": video_title, "comments": comments}

    except TimeoutException:
        print(f"[ERROR] Timeout while loading comments for '{video_title}'.")
    except Exception as e:
        print(f"[ERROR] Failed to scrape comments for video '{video_url}': {e}")
    finally:
        driver.quit()

    return {"title": video_title, "comments": []}


def worker(queue, results, lock):
    """Worker function to scrape comments from a video."""
    while not queue.empty():
        try:
            video_data = queue.get_nowait()  # Use get_nowait to avoid hanging
        except Exception:
            break  # Exit if the queue is empty

        video_url = video_data["url"]
        video_title = video_data["title"]
        comments_data = scrape_video_comments(video_url, video_title)
        if comments_data:
            with lock:
                results.append(comments_data)

        queue.task_done()


def start_comment_scrape_session(topics, thread_count=7):
    """Scrape comments for videos based on multiple topics."""
    print(f"[INFO] Starting comment scraping session for {len(topics)} topics.")

    # Step 1: Collect all video data for all topics concurrently
    all_video_data = []
    connect_to_vpn()

    print("[INFO] Collecting video URLs for all topics...")

    # Multithreaded scraping of video URLs
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = {executor.submit(scrape_video_urls, topic): topic for topic in topics}

        for future in futures:
            topic = futures[future]
            try:
                video_data = future.result()
                if video_data:
                    all_video_data.extend(video_data)
            except Exception as e:
                print(f"[ERROR] Failed to scrape video URLs for topic '{topic}': {e}")

    print(f"[INFO] Total videos collected for scraping: {len(all_video_data)}")

    # Step 2: Distribute comment scraping tasks
    video_queue = Queue()
    results = []
    lock = Lock()

    for video_data in all_video_data:
        video_queue.put(video_data)

    print(f"[INFO] Starting comment scraping for {len(all_video_data)} videos using {thread_count} threads.")

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for _ in range(thread_count):
            executor.submit(worker, video_queue, results, lock)

    video_queue.join()
    disconnect_vpn()

    # Step 3: Store results in the database
    print("[INFO] Storing scraped comments in database...")
    try:
        for result in results:
            if result["comments"]:  # Only save if there are comments
                save_comments_batch(result["comments"], result["title"])
        print("[INFO] Successfully stored comments in MongoDB.")
    except Exception as e:
        print(f"[ERROR] Failed to store comments in database: {e}")

    print(f"[INFO] Comment scraping session completed. Total videos processed: {len(results)}")


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
