def parse_likes(likes_string):
    try:
        # Ensure the input is a string
        if isinstance(likes_string, int):
            return likes_string  # It's already an integer

        # Remove newline characters and extra spaces
        cleaned_string = likes_string.replace('\n', '').replace(' ', '')

        # Parse likes string
        if 'K' in cleaned_string:
            value = float(cleaned_string.replace('K', '')) * 1_000
        elif 'M' in cleaned_string:
            value = float(cleaned_string.replace('M', '')) * 1_000_000
        elif 'B' in cleaned_string:
            value = float(cleaned_string.replace('B', '')) * 1_000_000_000
        else:
            value = int(''.join(filter(str.isdigit, cleaned_string)))

        return int(value)
    except ValueError as e:
        print(f"[ERROR] Failed to parse likes string: {likes_string} - {e}")
        return 0  # Return a fallback value instead of None

    
def parse_view_count(view_count_string):
    try:
        cleaned_string = ''.join(filter(str.isdigit, view_count_string))
        return int(cleaned_string)
    except ValueError as e:
        print(f"[ERROR] Failed to parse view count string: {view_count_string} - {e}")
        return 0  # Return 0 if view count parsing fails

def convert_to_int(number_string):
    try:
        # If it's already an integer, return it directly
        if isinstance(number_string, int):
            return number_string

        # Remove commas and convert to integer
        return int(number_string.replace(',', ''))
    except ValueError as e:
        print(f"[ERROR] Failed to convert string to int: {number_string} - {e}")
        return 0  # Return 0 as fallback in case of conversion failure