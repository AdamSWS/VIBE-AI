import requests
from deep_translator import GoogleTranslator
import logging
import os
from dotenv import load_dotenv
from langdetect import detect
from google_trends import get_randomized_youtube_trending_topics

# Load environment variables
load_dotenv()

# Check if API key is loaded
API_KEY = os.getenv("YOUTUBE_API_KEY")
print(f"[DEBUG] Loaded API_KEY: {'set' if API_KEY else 'not set'}")

if not API_KEY:
    print("[ERROR] API_KEY is not set. Ensure your .env file has the correct key and is loaded.")
    exit(1)

def check_api_quota():
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&maxResults=1&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 403 and "quotaExceeded" in response.text:
        print("[INFO] API quota exceeded. Change boolean in main.py to false to use Selenium Web Scraper. Exiting script.")
        return False
    return True

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Translator
translator = GoogleTranslator(source='auto', target='en')

# Searches for videos on YouTube based on a query
def search_videos(query, max_results=10):
    print(f"[DEBUG] Searching for videos with query: {query}")
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults={max_results}&key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        print("[DEBUG] Video search successful.")
        return response.json().get('items', [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Get comments for a specific video and translate them if necessary
def get_video_comments(video_id, video_title, max_comments=400, batch_size=200):
    comments = []
    next_page_token = None
    print(f"[DEBUG] Fetching comments for video ID: {video_id}")

    while len(comments) < max_comments:
        url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=100&key={API_KEY}"

        if next_page_token:
            url += f"&pageToken={next_page_token}"

        response = requests.get(url)

        if response.status_code == 200:
            print("[DEBUG] Comments fetched successfully.")
            data = response.json()
            items = data.get('items', [])
            if not items:
                print("[INFO] No more comments available.")
                break

            for item in items:
                if len(comments) >= max_comments:
                    break

                try:
                    comment_data = item['snippet']['topLevelComment']['snippet']
                    comment_id = item['id']
                    original_text = comment_data['textDisplay']

                    # Detect the language of the original comment
                    detected_language = detect(original_text)
                    print(f"[DEBUG] Detected language for comment ID {comment_id}: {detected_language}")

                    # Attempt translation only if the detected language is not English
                    if detected_language != 'en':
                        translated_text = translator.translate(original_text)
                    else:
                        translated_text = original_text

                    comment = {
                        'comment_id': comment_id,
                        'video_id': video_id,
                        'author': comment_data['authorDisplayName'],
                        'original_text': original_text,
                        'translated_text': translated_text,
                        'like_count': comment_data['likeCount'],
                        'timestamp': comment_data['publishedAt'],
                    }
                    comments.append(comment)

                except KeyError as e:
                    print(f"[ERROR] KeyError for comment item: {e}")
                    continue

            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
        
        elif response.status_code == 403:
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            if 'commentsDisabled' in error_message:
                print(f"Comments are disabled for video ID {video_id}. Skipping this video.")
                return []
            print(f"403 Error for video ID {video_id}: {error_message}")
            break
        
        else:
            print(f"Error {response.status_code} for video ID {video_id}: {response.text}")
            break

    return comments[:max_comments]  

# Helper function to process and translate a single comment
def process_comment(comment_data, video_id):
    original_text = comment_data['textDisplay']

    # Detect the language of the original comment
    try:
        detected_language = detect(original_text)
        print(f"[DEBUG] Detected language for comment ID {comment_data['id']}: {detected_language}")
    except Exception as e:
        print(f"Language detection failed for comment ID {comment_data['id']}: {e}")
        detected_language = 'unknown'

    # Attempt translation only if the detected language is not English
    if detected_language != 'en':
        try:
            translated_text = translator.translate(original_text)
        except Exception as e:
            print(f"Translation failed for comment ID {comment_data['id']}: {e}")
            translated_text = original_text
    else:
        translated_text = original_text  # No need to translate if it's already in English

    return {
        'comment_id': comment_data['id'],
        'video_id': video_id,
        'author': comment_data['authorDisplayName'],
        'original_text': original_text,
        'translated_text': translated_text,
        'like_count': comment_data['likeCount'],
        'timestamp': comment_data['publishedAt'],
    }

# Main execution for testing
if __name__ == "__main__":
    trending_topics = get_randomized_youtube_trending_topics(n_topics=5)
    print(f"[DEBUG] Trending topics: {trending_topics}")

    for topic in trending_topics:
        search_results = search_videos(topic, max_results=5)
        if search_results:
            for result in search_results:
                video_id = result['id']['videoId']
                video_title = result['snippet']['title']
                get_video_comments(video_id, video_title)
        else:
            print(f"[INFO] No videos found for topic: {topic}")
