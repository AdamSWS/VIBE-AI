import time
import re
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from deep_translator import GoogleTranslator
from langdetect import detect

# Create a new Chrome driver with specific options
def create_driver():
    chrome_options = webdriver.ChromeOptions()
    driver_path = os.path.abspath("./web_scraper/driver/chromedriver")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    service = Service(driver_path)
    service.startup_timeout = 30
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"[ERROR] Failed to create driver: {e}")
        return None

# Sanitize a filename by removing forbidden characters
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# Random delay function
def random_delay(base=2, variability=3):
    time.sleep(base + random.uniform(0, variability))

# Translate text if it's not in English
def translate_text(text):
    try:
        detected_language = detect(text)
        if detected_language != 'en':
            translated_text = GoogleTranslator(source='auto', target='en').translate(text)
        else:
            translated_text = text
        return translated_text
    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return text

# Search for a YouTube video by topic and return the URL of the first result
def scrape_video_data_from_search(topic):
    driver = create_driver()
    search_url = f"https://www.youtube.com/results?search_query={topic}"
    driver.get(search_url)
    time.sleep(5)

    try:
        # Locate the first video result and retrieve its URL
        first_video = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '(//*[@id="video-title"])[1]'))
        )
        video_url = first_video.get_attribute('href')
        if video_url:
            print(f"[INFO] Found video URL: {video_url}")
            return scrape_video_data(driver, video_url)
        else:
            print(f"[WARNING] No video URL found for topic: {topic}")
            return None
    except exceptions.NoSuchElementException as e:
        print(f"[ERROR] Failed to find video for topic '{topic}': {e}")
        return None
    finally:
        driver.quit()

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
        return {
            "title": title,
            "comments": comments[:max_comments]
        }

    except exceptions.WebDriverException as e:
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

# Main execution
if __name__ == "__main__":
    topic = "sample topic"
    video_data = scrape_video_data_from_search(topic)
    if video_data:
        print(f"Scraped video data: {video_data}")
