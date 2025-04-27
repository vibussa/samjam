import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
import time
import os
import json

# ---------- CONFIG ----------
API_KEY = "AIzaSyAw5XhJLxvtZhkK-r24NI9AtdA3FHRdMlg"
REGION_CODE = "IN"
MAX_RESULTS = 50
REFRESH_INTERVAL = 3600  # seconds (1 hour)
HISTORY_FILE = "upload_history.json"

# ---------- YOUTUBE API SETUP ----------
youtube = build('youtube', 'v3', developerKey=API_KEY)

# ---------- FETCH TRENDING VIDEOS ----------
def get_trending_videos():
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=REGION_CODE,
            maxResults=MAX_RESULTS
        )
        response = request.execute()
        return response['items']
    except HttpError as e:
        st.error("❌ Failed to fetch trending videos. Please check your API key, quota limits, or region settings.")
        return []

# ---------- MAIN APP ----------
st.set_page_config(page_title="YouTube Trending Dashboard", layout="wide")
st.title("🔥 YouTube Trending Dashboard (India)")

with st.spinner('Fetching real-time trending videos...'):
    videos = get_trending_videos()

if not videos:
    st.warning("⚡ No trending videos available right now. Please refresh after some time!")
    st.stop()

# ---------- EXTRACT HASHTAGS FROM TITLES AND DESCRIPTIONS ----------
# (Rest of your code remains unchanged)

# Keep the rest of your code exactly as it is after this point.
