import random
from pytrends.request import TrendReq

# Initialize pytrends globally
pytrends = TrendReq(hl='en-US', tz=360)

def get_all_specified_regions():
    """Return the full list of specified regions to be covered."""
    return [
        'AR', 'AU', 'AT', 'BE', 'BR', 'BG', 'CA', 'CL', 'CO', 'HR', 'CZ', 'EG', 
        'EE', 'FI', 'FR', 'DE', 'GR', 'HK', 'HU', 'IN', 'ID', 'IE', 'IL', 'IT', 
        'JP', 'KE', 'KR', 'LV', 'LT', 'MY', 'MX', 'NL', 'NZ', 'NG', 'NO', 'PK', 
        'PE', 'PL', 'PT', 'RO', 'SA', 'RS', 'SG', 'SK', 'SI', 'ZA', 'ES', 'SE', 
        'CH', 'TW', 'TH', 'TR', 'UA', 'AE', 'GB', 'US', 'UY', 'VN'
    ]

def get_youtube_trending_topics_sampled_regions(n_topics=2):
    """Fetch trending topics from random regions with categories and return a list of topics."""
    categories = [
        'Arts & Entertainment', 'Autos & Vehicles', 'Beauty & Fitness', 'Books & Literature', 'Business & Industrial',
        'Computers & Electronics', 'Finance', 'Food & Drink', 'Games', 'Health', 'Hobbies & Leisure', 'Home & Garden',
        'Internet & Telecom', 'Jobs & Education', 'Law & Government', 'News', 'Online Communities', 'People & Society',
        'Pets & Animals', 'Real Estate', 'Reference', 'Science', 'Shopping', 'Sports', 'Travel'
    ]

    regions = random.sample(get_all_specified_regions(), 3)  # Sample 3 regions randomly
    all_topics = set()

    for region in regions:
        try:
            selected_category = random.choice(categories)
            print(f"[DEBUG] Selected category: {selected_category} for region: {region}")
            
            # Fetch trending topics using pytrends top_charts
            trending_searches_df = pytrends.top_charts(2023, hl='en-US', tz=360, geo=region)
            print(f"[DEBUG] Fetched trending searches for region {region}. DataFrame received: {trending_searches_df is not None}")

            if trending_searches_df is None or 'title' not in trending_searches_df:
                print(f"[WARNING] No data or 'title' column missing for region: {region} in category: {selected_category}. Retrying without category.")
                trending_searches_df = pytrends.top_charts(2023, hl='en-US', tz=360, geo=region)

            if trending_searches_df is not None and 'title' in trending_searches_df:
                for topic in trending_searches_df['title'].tolist():
                    all_topics.add(topic)

        except Exception as e:
            print(f"[ERROR] Error fetching topics for region {region}: {e}")

    # Filter out sports-related topics and return a list of diverse topics
    sports_keywords = ['football', 'soccer', 'basketball', 'tennis', 'cricket', 'baseball', 'rugby']
    diverse_topics = [
        topic for topic in all_topics
        if not any(keyword in topic.lower() for keyword in sports_keywords)
        and ('vs' not in topic.lower() or random.random() >= 0.9)
    ]
    
    random.shuffle(diverse_topics)
    return diverse_topics[:n_topics]

# Example usage
if __name__ == "__main__":
    topics = get_youtube_trending_topics_sampled_regions()
    print("Randomized YouTube trending topics:", topics)
