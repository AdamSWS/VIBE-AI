import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common import exceptions

# Create a new Chrome driver with specific options
def create_driver():
    chrome_options = webdriver.ChromeOptions()
    driver_path = "YOUR DRIVER PATH"
    driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    return driver

# Sanitize a filename by removing forbidden characters
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# Search for a YouTube video by topic and return the URL of the first result
def scrape_video_data_from_search(topic):
    driver = create_driver()
    search_url = f"https://www.youtube.com/results?search_query={topic}"
    driver.get(search_url)
    time.sleep(5)  # Wait for page to load

    try:
        # Locate the first video result and retrieve its URL
        first_video = driver.find_element(By.XPATH, '(//*[@id="video-title"])[1]')
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
        driver.quit()  # Close the driver

# Scrape the title, comments, and likes for each comment from a YouTube video page
def scrape_video_data(driver, url, max_comments=400):
    print(f"[INFO] Starting scrape for video page: {url}")
    driver.get(url)
    driver.maximize_window()
    time.sleep(5)  # Wait for page to load

    try:
        # Skip the video if it is a YouTube Shorts video
        if "/shorts/" in url:
            print(f"[INFO] Skipping video '{url}' - This is a YouTube Shorts video.")
            return None

        # Get the title of the video
        title = driver.find_element(By.XPATH, '//*[@id="container"]/h1/yt-formatted-string').text
        print(f"[INFO] Video title extracted: {title}")

        # Check if comments are enabled
        try:
            comment_count_text = driver.find_element(By.XPATH, '//*[@id="count"]/yt-formatted-string').text
            if "Comments are turned off" in comment_count_text or comment_count_text == "0":
                print(f"[INFO] Skipping video '{title}' - Comments are disabled or there are 0 comments.")
                return None
        except exceptions.NoSuchElementException:
            print(f"[INFO] Skipping video '{title}' - Comment section not found or comments are disabled.")
            return None

        # Scroll to the comments section to start loading comments
        comment_section = driver.find_element(By.XPATH, '//*[@id="comments"]')
        driver.execute_script("arguments[0].scrollIntoView();", comment_section)
        time.sleep(7)  # Allow comments section to load

        # Collect comments until max_comments is reached
        comments = []
        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        # Scroll and collect comments until we reach the max_comments limit or there are no new comments
        while len(comments) < max_comments:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # Allow the page to load more comments

            # Extract comments and their like counts
            comment_elems = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
            like_elems = driver.find_elements(By.XPATH, '//*[@id="vote-count-middle"]')

            # Append each comment and its like count to the comments list
            for comment, likes in zip(comment_elems, like_elems):
                like_count = likes.text if likes.text else "0"  # Default to 0 if no likes
                comments.append({
                    'text': comment.text,
                    'likes': like_count
                })

                # Print batches of comments for tracking progress
                if len(comments) % 50 == 0 or len(comments) >= max_comments:
                    print(f"[INFO] Sending batch of comments (Total so far: {len(comments)}):")
                    for i in range(len(comments) - 50, len(comments)):
                        print(f"{comments[i]}")
                    print("\n")

            # Stop scrolling if no new comments are loaded
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Print the final batch if any comments remain
        if len(comments) % 50 != 0:
            remaining_comments = len(comments) % 50
            print(f"[INFO] Sending final batch of {remaining_comments} comments:")
            for i in range(len(comments) - remaining_comments, len(comments)):
                print(f"{comments[i]}")
            print("\n")

        # Return the video title and collected comments
        return {
            "title": title,
            "comments": comments[:max_comments]  # Limit to max_comments if exceeded
        }

    except exceptions.NoSuchElementException as e:
        print(f"[ERROR] An error occurred while scraping {url}: {e}")
        return None
    finally:
        driver.quit()  # Close the driver

# Main execution
if __name__ == "__main__":
    topic = "sample topic"
    video_data = scrape_video_data_from_search(topic)
    print(f"Scraped video data: {video_data}")
