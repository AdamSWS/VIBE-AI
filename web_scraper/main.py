import time
from pymongo import MongoClient
from db_conn import get_db_client
from comment_analysis import calculate_adjusted_score
from google_trends import get_youtube_trending_topics_sampled_regions
from youtube_scraper import scrape_video_data_from_search
from db_handler import push_to_database
from utils import load_keywords

def main():
    # Connect to MongoDB
    db = get_db_client()
    try:
        # Check available collections to confirm connection
        collections = db.list_collection_names()
        print("Connected to MongoDB successfully.")
        print("Collections available:", collections)
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
        return

    # Load keywords for analysis
    keywords = load_keywords()
    # Define weights and threshold for comment scoring (IGNORE THIS FOR NOW)
    weights = {'likes': 0.25, 'length': 0.05, 'keywords': 0.7}
    threshold = 0.3

    # Get a list of trending topics
    trending_topics = get_youtube_trending_topics_sampled_regions(n_topics=5)

    # Process each topic
    for topic in trending_topics:
        print(f"\n[INFO] Processing topic: {topic}")

        # Scrape video data for the topic
        video_data = scrape_video_data_from_search(topic)

        # If video data was successfully retrieved
        if video_data:
            # Push video data to the database
            push_to_database(video_data)

        # Wait for 1 second before processing the next topic to avoid rate-limiting
        time.sleep(1)

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
