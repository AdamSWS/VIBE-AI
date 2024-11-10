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

def get_randomized_youtube_trending_topics(n_topics=5):
    """Fetch randomized trending topics from different regions with random categories."""
    categories = [
        'Arts & Entertainment', 'Autos & Vehicles', 'Beauty & Fitness', 'Books & Literature', 'Business & Industrial',
        'Computers & Electronics', 'Finance', 'Food & Drink', 'Games', 'Health', 'Hobbies & Leisure', 'Home & Garden',
        'Internet & Telecom', 'Jobs & Education', 'Law & Government', 'News', 'Online Communities', 'People & Society',
        'Pets & Animals', 'Real Estate', 'Reference', 'Science', 'Shopping', 'Sports', 'Travel'
    ]
    # Randomly pick 3 regions
    regions = random.sample(get_all_specified_regions(), 3)
    all_topics = set()

    for region in regions:
        try:
            selected_category = random.choice(categories)
            print(f"[DEBUG] Selected category: {selected_category} for region: {region}")

            # Fetch trending topics using pytrends (mocked for category)
            trending_searches_df = pytrends.top_charts(2023, hl='en-US', tz=360, geo=region)
            print(f"[DEBUG] Fetched trending searches for region {region}. DataFrame received: {trending_searches_df is not None}")

            if trending_searches_df is not None and 'title' in trending_searches_df:
                for topic in trending_searches_df['title'].tolist():
                    all_topics.add(topic)

        except Exception as e:
            print(f"[ERROR] Error fetching topics for region {region}: {e}")

    # Shuffle and diversify topics to avoid similar results each time
    diverse_topics = list(all_topics)
    random.shuffle(diverse_topics)
    return diverse_topics[:n_topics]

# Example usage
if __name__ == "__main__":
    topics = get_randomized_youtube_trending_topics()
    print("Randomized YouTube trending topics:", topics)
