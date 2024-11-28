from logging import exception
import time
import requests
import random
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from langdetect import detect
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from db.db import get_db, store_items_to_collection
from scraper.driver import create_driver

from trends.google_trends import get_randomized_youtube_trending_topics
from vpn.vpn_handler import connect_to_vpn, disconnect_vpn

USE_API_FOR_COMMENTS = False 

def search_videos(query, max_results=5):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults={max_results}&key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()['items']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_video_comments(video_id, max_results=100):
    comments = []
    next_page_token = None

    while True:
        url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={API_KEY}"

        if next_page_token:
            url += f"&pageToken={next_page_token}"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                comment_data = item['snippet']['topLevelComment']['snippet']
                comment = {
                    'comment_id': item['id'],
                    'video_id': video_id,
                    'author': comment_data['authorDisplayName'],
                    'text': comment_data['textDisplay'],
                    'like_count': comment_data['likeCount'],
                    'timestamp': comment_data['publishedAt'],
                }
                comments.append(comment)

            next_page_token = data.get('nextPageToken')

            if not next_page_token:
                break
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break

    return comments

def fetch_trending_topics(n_topics=5):
    """Fetch a randomized set of trending topics.""" 
    try:
        trending_topics = get_randomized_youtube_trending_topics(n_topics=n_topics)
        print(f"[INFO] Retrieved trending topics: {trending_topics}")
        return trending_topics
    except Exception as e:
        print(f"[ERROR] Failed to fetch trending topics: {e}")
        return []


def translate_text(text):
    """Translate a given text into English if it's not already in English."""
    try:
        detected_language = detect(text)
        if detected_language != 'en':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return text


def translate_comments(comments):
    """Translate comments sequentially."""
    for comment in comments:
        try:
            comment['translated_text'] = translate_text(comment['original_text'])
        except Exception as e:
            print(f"[ERROR] Translation failed for comment: {e}")


def parse_like_count(like_text):
    """Parse the like count text into an integer value."""
    try:
        if 'K' in like_text:
            return int(float(like_text.replace('K', '')) * 1000)
        elif 'M' in like_text:
            return int(float(like_text.replace('M', '')) * 1_000_000)
        elif like_text.isdigit():
            return int(like_text)
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to parse like count: {e}")
        return 0


def scroll_to_load_comments(driver, max_comments=800):
    """Scroll the YouTube page to load comments dynamically."""
    comments, seen_comments = [], set()
    retries = 0

    while len(comments) < max_comments:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(0.09)

        comment_elems = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
        like_elems = driver.find_elements(By.XPATH, '//*[@id="vote-count-middle"]')

        for i in range(len(comment_elems)):
            original_text = comment_elems[i].text.strip()
            if original_text not in seen_comments:
                seen_comments.add(original_text)
                like_count = parse_like_count(like_elems[i].text.strip()) if i < len(like_elems) else 0
                comments.append({
                    'original_text': original_text,
                    'translated_text': None,
                    'like_count': like_count
                })
                if len(comments) >= max_comments:
                    break

        if retries >= 3 or len(comments) == len(seen_comments):
            break

    return comments

# Random delay function
def random_delay(base=2, variability=3):
    time.sleep(base + random.uniform(0, variability))

# Scrape the title, comments, and translate them
def scrape_video_data(driver, url, max_comments=400):
    print(f"[INFO] Starting scrape for video page: {url}")
    driver.get(url)
    time.sleep(5)

    try:
        # Skip if the video is a YouTube Shorts video
        if "/shorts/" in url:
            print(f"[INFO] Skipping video '{url}' - This is a YouTube Shorts video.")
            return None

        # Get the title of the video
        title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/h1/yt-formatted-string'))
        ).text

        # Check if the comment section exists
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="comments"]'))
        )

        # Scroll to the comments section to start loading comments
        driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.XPATH, '//*[@id="comments"]'))
        time.sleep(5)
        # Collect comments
        comments = []
        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        while len(comments) < max_comments:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            random_delay(2, 3)

            # Extract comments and their like counts
            comment_elems = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
            like_elems = driver.find_elements(By.XPATH, '//*[@id="vote-count-middle"]')

            if not comment_elems:
                print(f"[INFO] No comments found on the video '{title}'.")
                break

            for comment, likes in zip(comment_elems, like_elems):
                original_text = comment.text
                translated_text = translate_text(original_text)

                like_count = likes.text if likes.text else "0"
                comments.append({
                    'comment_id': None,
                    'video_id': url,
                    'original_text': original_text,
                    'translated_text': translated_text,
                    'like_count': like_count,
                })

                if len(comments) >= max_comments:
                    break

            # Stop scrolling if no new comments are loaded
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        print(f"[INFO] Collected {len(comments)} comments.")
        print(comments)
        return {
            "title": title,
            "comments": comments[:max_comments]
        }

    except exception.WebDriverException as e:
        print(f"[ERROR] WebDriver exception: {e}")
        driver.quit()
        return None
    except Exception as e:
        print(f"[ERROR] General error during scrape: {e}")
        driver.quit()
        return None
    finally:
        if driver:
            driver.quit()


def scrape_video_data_from_search(topic):
    """Search for a topic on YouTube and scrape data from the first video."""
    driver = create_driver()
    if not driver:
        return None

    try:
        search_url = f"https://www.youtube.com/results?search_query={topic}"
        driver.get(search_url)
        print(f"[INFO] Searching for topic: {topic}")

        first_video = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '(//*[@id="video-title"])[1]'))
        )
        video_url = first_video.get_attribute('href')
        print(f"[INFO] Found video URL: {video_url}")

        return scrape_video_data(driver, video_url)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None
    finally:
        driver.quit()


def process_topic_with_api(topic, db):
    """Process a single topic using the YouTube API to fetch comments."""
    print(f"[INFO] Processing topic with API: {topic}")
    try:
        search_results = search_videos(topic, max_results=5)
        if search_results:
            for result in search_results:
                video_id = result['id'].get('videoId')
                video_title = result['snippet']['title']
                print(f"[INFO] Fetching comments for video ID: {video_id}, title: {video_title}")

                comments = get_video_comments(video_id, video_title)
                if comments:
                    collection = get_db("youtube_comments")
                    store_items_to_collection(collection, comments)
    except Exception as e:
        print(f"[ERROR] Error processing topic with API: {e}")


def process_topic_with_scraping(topic, db):
    """Process a single topic using web scraping to fetch comments."""
    print(f"[INFO] Processing topic with scraping: {topic}")
    try:
        video_data = scrape_video_data_from_search(topic)
        if video_data:
            comments = video_data['comments']
            if comments:
                collection = get_db("youtube_comments")
                store_items_to_collection(collection, comments)
    except Exception as e:
        print(f"[ERROR] Error during scraping for topic {topic}: {e}")


def process_topics(trending_topics, db):
    """Process a list of trending topics."""
    for topic in trending_topics:
        if USE_API_FOR_COMMENTS:
            process_topic_with_api(topic, db)
        else:
            process_topic_with_scraping(topic, db)
        time.sleep(1)  # Avoid rate-limiting


def start_comment_scrape_session(threads=7, topics=None):
    """Start a session to scrape comments based on provided or trending topics."""
    print(f"[INFO] Starting comment scraping session with {threads} thread(s)...")
    topics = topics or fetch_trending_topics()
    all_comments = []

    try:
        connect_to_vpn()

        db = get_db("youtube_comments")
        process_topics(topics, db)

    except Exception as e:
        print(f"[ERROR] Session error: {e}")

    finally:
        disconnect_vpn()

    print(f"[INFO] Finished scraping session.")
    return all_comments

if __name__ == "__main__":
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
    topics = ['Reference', 'News', 'Sports', 'Pets & Animals', 'Shopping']
    print(f"[INFO] Topics to scrape: {topics}")
    trending_video_stats = start_comment_scrape_session(threads=num_threads, topics=topics)

    if trending_video_stats:
        print("[INFO] Scraped Video Details:")
        for video in trending_video_stats:
            print(video)