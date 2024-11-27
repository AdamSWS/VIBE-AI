"""
This file uses the PyTrends API to fetch trending topics for specified regions
and categories, filtering and randomizing the results for YouTube-related 
trends. It provides functions to retrieve regions, filter previously seen 
topics, fetch regional trends, and generate random topics from predefined categories.
"""

import random
from pytrends.request import TrendReq

# Initialize pytrends globally
pytrends = TrendReq(hl='en-US', tz=360)
previous_topics = set()

def get_all_specified_regions():
    regions = ['US', 'CA', 'GB', 'AU', 'IN']
    print(f"[INFO] Regions specified for trending topic search: {regions}")
    return regions

def filter_topics(topics, n_topics):
    global previous_topics
    filtered_topics = []
    for topic in topics:
        # Skip if the topic is already in the previous topics set
        if topic.lower() in previous_topics:
            continue
        # Add to the filtered list and update the previously seen topics
        filtered_topics.append(topic)
        previous_topics.add(topic.lower())
        if len(filtered_topics) >= n_topics:
            break
    return filtered_topics

def fetch_trending_topics_for_region(region, categories):
    try:
        print(f"[INFO] Fetching trending topics for region: {region}")
        selected_category = random.choice(categories)
        print(f"[DEBUG] Selected category: {selected_category} for region: {region}")

        # Fetch trending topics using pytrends
        print(f"[INFO] Connecting to Pytrends API for region {region}...")
        trending_searches_df = pytrends.top_charts(2023, hl='en-US', tz=360, geo=region)
        print(f"[INFO] Received data for region {region}. Processing...")

        if trending_searches_df is not None and 'title' in trending_searches_df:
            topics = trending_searches_df['title'].tolist()
            print(f"[INFO] Extracted {len(topics)} topics for region {region}: {topics}")
            return topics
        else:
            print(f"[WARNING] No trending topics found for region {region}.")
    except Exception as e:
        print(f"[ERROR] Error fetching topics for region {region}: {e}")
    return []

def get_randomized_youtube_trending_topics(n_topics=5):
    categories = [
        'Arts & Entertainment', 'Autos & Vehicles', 'Beauty & Fitness', 'Books & Literature', 'Business & Industrial',
        'Computers & Electronics', 'Finance', 'Food & Drink', 'Games', 'Health', 'Hobbies & Leisure', 'Home & Garden',
        'Internet & Telecom', 'Jobs & Education', 'Law & Government', 'News', 'Online Communities', 'People & Society',
        'Pets & Animals', 'Real Estate', 'Reference', 'Science', 'Shopping', 'Sports', 'Travel'
    ]

    print("[INFO] Selecting random topics...")
    return random.sample(categories, min(n_topics, len(categories)))

# Example usage
if __name__ == "__main__":
    print("[INFO] Starting YouTube trending topics scraper.")
    topics = get_randomized_youtube_trending_topics()
    print("[INFO] Final Trending Topics:")
    for i, topic in enumerate(topics, 1):
        print(f"{i}. {topic}")
