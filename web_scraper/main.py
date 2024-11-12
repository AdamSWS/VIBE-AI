import time
from db_conn import get_db_client
from google_trends import get_randomized_youtube_trending_topics
from comment_script import get_video_comments, search_videos, check_api_quota
from youtube_scraper import scrape_video_data_from_search
from db_handler import save_comments_batch

# Variable to toggle between using scraping and YouTube API
USE_API_FOR_COMMENTS = True

def main():
    print("[INFO] Starting main function...")

    # Connect to MongoDB
    try:
        db = get_db_client()
        print("[INFO] MongoDB connection established.")
        collections = db.list_collection_names()
        print("Collections available:", collections)
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
        return
    
    # Process each topic in a loop until the API quota is exhausted
    while True:
        try:
            trending_topics = get_randomized_youtube_trending_topics(n_topics=5)
            print(f"[INFO] New set of trending topics: {trending_topics}")
            for topic in trending_topics:
                print(f"\n[INFO] Processing topic: {topic}")
                if USE_API_FOR_COMMENTS:
                    print("[INFO] Using YouTube API to fetch comments.")
                    search_results = search_videos(topic, max_results=5)
                    if search_results:
                        for result in search_results:
                            video_id = result['id'].get('videoId')
                            video_title = result['snippet']['title']
                            print(f"[INFO] Fetching comments for video ID: {video_id}, title: {video_title}")

                            # Get video comments in batches and save them
                            try:
                                comments = get_video_comments(video_id, video_title)
                                if comments:
                                    save_comments_batch(comments, video_title, db)
                            except Exception as e:
                                print(f"[ERROR] Error fetching comments for video ID {video_id}: {e}")
                                if USE_API_FOR_COMMENTS and not check_api_quota():
                                    return
                    else:
                        print("[INFO] No search results returned for topic:", topic)
                        if USE_API_FOR_COMMENTS and not check_api_quota():
                            return
                else:
                    try: 
                        video_data = scrape_video_data_from_search(topic)
                        if video_data:
                            video_title = video_data['title']
                            comments = video_data['comments']
                            if comments:
                                save_comments_batch(comments, video_title, db)
                            else:
                                print("[WARNING] No valid video title or comments found.")
                    except Exception as e:
                        print("[ERROR] No data has been scraped:", e)
                        return
                # Wait to avoid rate-limiting
                time.sleep(1)

        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
            if "quotaExceeded" in str(e):
                print("[INFO] API quota exceeded. Exiting script.")
                break

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in main execution: {e}")
