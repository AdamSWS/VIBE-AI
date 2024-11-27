"""
This file automates the scraping of YouTube video metadata, including title,
description, tags, upload date, view count, and likes, using Selenium WebDriver.
"""

from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .driver import create_driver
from queue import Queue
from threading import Lock
from .stats_parser import parse_likes, parse_view_count

MAX_VIDEOS = 35


def scrape_video_details(video_url):
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

        # Scrape tags from meta keywords
        try:
            tags = driver.execute_script(
                "return document.querySelector('meta[name=\"keywords\"]').getAttribute('content');"
            )
            tags = tags.split(",") if tags else []
        except Exception:
            tags = []

        try:
            # Assuming the upload date is the first bold formatted-string span
            upload_date = driver.find_element(By.XPATH, '//span[@class="style-scope yt-formatted-string bold"][3]').text
        except Exception:
            upload_date = "Unknown"

        try:
            # Get the view count from the 'div#view-count' container
            view_count = driver.find_element(By.XPATH, '//span[@class="style-scope yt-formatted-string bold"][1]').text
        except Exception as e:
            print(f"[ERROR] Failed to fetch view count: {e}")
            view_count = "Unknown"

        # Scrape likes
        try:
            likes = driver.find_element(By.XPATH, '//*[@id="top-level-buttons-computed"]/segmented-like-dislike-button-view-model/yt-smartimation/div/div/like-button-view-model/toggle-button-view-model/button-view-model/button/div[2]').text
        except Exception:
            likes = "No description available"
        
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

def worker(queue, results, lock):
    while not queue.empty():
        video_url = queue.get()
        if video_url is None:  # Exit condition
            break

        video_data = scrape_video_details(video_url)
        if video_data:
            with lock:
                results.append(video_data)

        queue.task_done()

def scrape_trending_videos(topic, thread_count=10):
    print(f"[INFO] Starting YouTube video scraper for topic: {topic}")
    driver = create_driver()

    if not driver:
        print("[ERROR] WebDriver could not be created. Exiting.")
        return []

    try:
        # Navigate to the YouTube search page for the topic
        search_url = f"https://www.youtube.com/results?search_query={'+'.join(topic.split())}"
        driver.get(search_url)

        # Wait for video elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//ytd-video-renderer'))
        )

        videos = driver.find_elements(By.XPATH, '//ytd-video-renderer')[:MAX_VIDEOS]
        print(f"[INFO] Found {len(videos)} videos for topic '{topic}'.")

        # Extract video URLs
        video_urls = []
        for video in videos:
            try:
                video_url = video.find_element(By.XPATH, './/a[@id="video-title"]').get_attribute("href")
                if "/shorts/" not in video_url:
                    video_urls.append(video_url)
            except Exception as e:
                print(f"[ERROR] Failed to extract video URL: {e}")

        # Prepare threading components
        video_queue = Queue()
        results = []
        lock = Lock()

        # Add video URLs to the queue
        for url in video_urls:
            video_queue.put(url)

        print(f"[INFO] Queue initialized with {len(video_urls)} videos.")

        # Create and start threads
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            for _ in range(thread_count):
                executor.submit(worker, video_queue, results, lock)

        # Wait for all tasks to complete
        video_queue.join()

        print(f"[INFO] Scraping completed for topic: {topic}. Total videos scraped: {len(results)}")
        return results

    except Exception as e:
        print(f"[ERROR] Failed to scrape videos for topic '{topic}': {e}")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    topics = ["Minimalist Art", "Independent Films", "Urban Street Art", "Theatre Acting Techniques", "Jazz Improvisation"]
    all_results = []
    for topic in topics:
        try: 
            topic_results = scrape_trending_videos(topic, 1)
            all_results.extend(topic_results)
        except Exception as e:
            print(f"[ERROR] Failed to scrape videos for topic '{topic}': {e}")
        finally:
            print(all_results)
