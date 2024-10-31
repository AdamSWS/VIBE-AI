# YouTube Data API Project

## Prerequisites

- Python 3.x installed on your system
- A Google account for accessing the Google Cloud Platform

## Installation

1. **Clone the repository** (or download the code):
   ```bash
   git clone git@github.com:AdamSWS/Youtube-Comment-Gathering.git
   cd Youtube-Comment-Gathering

2. Install the required Python packages: Run the following command to install dependencies from requirements.txt:
    ```bash
    pip install -r requirements.txt

## How to Create a Google Developer Account and Get a YouTube Data API v3 Key

### Create a Google Developer Account:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account (or create one if you don't have one).

### Create a New Project:
1. Click on the **Select a project** dropdown in the top navigation bar.
2. Click on **New Project** and give it a name (e.g., "YouTube API Project").
3. Click **Create**.

### Enable YouTube Data API v3:
1. In the **Navigation Menu**, go to **APIs & Services > Library**.
2. Search for "YouTube Data API v3" and click on it.
3. Click **Enable**.

### Create Credentials (Select Public Data if prompted):
1. Go to **APIs & Services > Credentials**.
2. Click **+ CREATE CREDENTIALS** and choose **API key**.
3. An API key will be generated and displayed. Copy this key.

### Set Up API Key in the Project:
Replace the `API_KEY` variable in the code with your API key:
   ```python
   API_KEY = "YOUR_API_KEY"
   ```

## Running the Project

1. Make sure your API key is properly set in the code.
2. Run the Python script:
   ```bash
   python comment_script.py
