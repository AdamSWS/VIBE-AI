"""
This file initializes a Selenium WebDriver for web scraping tasks like parsing
YouTube comments. It configures the ChromeDriver with options to disable 
unnecessary features, handle permissions, and support headless operation.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import subprocess

def create_driver():
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--incognito")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-images")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")

        # Verify and configure the ChromeDriver path
        driver_path = os.path.abspath("./src/video_scraper/driver/chromedriver")
        print(f"[DEBUG] Driver Path: {driver_path}")
        if not os.access(driver_path, os.X_OK):
            subprocess.run(["chmod", "+x", driver_path], check=True)

        # Initialize the WebDriver
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    except Exception as e:
        print(f"[ERROR] Failed to create WebDriver: {e}")
        return None
