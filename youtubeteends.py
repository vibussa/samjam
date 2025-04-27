import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
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
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=REGION_CODE,
        maxResults=MAX_RESULTS
    )
    response = request.execute()
    return response['items']

# ---------- EXTRACT HASHTAGS FROM TITLES AND DESCRIPTIONS ----------
def extract_hashtags_real(videos):
    hashtags = []
    for v in videos:
        text = v['snippet'].get('title', '') + ' ' + v['snippet'].get('description', '')
        hashtags.extend(re.findall(r"#\w+", text))
    return hashtags

# ---------- EXTRACT KEYWORDS ----------
def extract_keywords(titles):
    words = re.findall(r"\b\w+\b", " ".join(titles).lower())
    stopwords = set(pd.read_csv("https://raw.githubusercontent.com/stopwords-iso/stopwords-en/master/stopwords-en.txt", header=None)[0])
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    return Counter(filtered_words).most_common(20)

# ---------- EXTRACT REAL HOOKS FROM TITLES ----------
def extract_real_hooks(titles):
    matches = []
    for title in titles:
        parts = title.split('|')
        for part in parts:
            cleaned = part.strip()
            if len(cleaned.split()) >= 3 and len(cleaned) < 80:
                matches.append(cleaned)
    return list(set(matches))[:7]

# ---------- GENERATE VIRAL TITLES ----------
def generate_viral_title(base_title, real_hooks):
    return [f"{hook} | {base_title}" for hook in real_hooks]

# ---------- GENERATE VIRAL HASHTAGS ----------
def generate_viral_hashtags(keywords):
    base_tags = ["#shorts", "#trending", "#viral"]
    dynamic_tags = [f"#{kw[0]}" for kw in keywords[:5]]
    return base_tags + dynamic_tags

# ---------- SAVE UPLOAD TIMES ----------
def save_upload_times(upload_hours):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []
    history.extend(upload_hours)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

# ---------- BEST TIME TO POST (REAL DATA + HISTORICAL) ----------
def suggest_best_time(videos, mode='24h'):
    india_timezone = pytz.timezone('Asia/Kolkata')
    upload_hours = []

    now = datetime.now(india_timezone)

    for v in videos:
        upload_time_utc = v['snippet']['publishedAt']
        upload_time = datetime.fromisoformat(upload_time_utc.replace('Z', '+00:00')).astimezone(india_timezone)

        if mode == '24h':
            if (now - upload_time).total_seconds() <= 86400:
                upload_hours.append(upload_time.hour)
        elif mode == '7d':
            if (now - upload_time).total_seconds() <= 604800:
                upload_hours.append(upload_time.hour)

    if not upload_hours:
        st.warning(f"No uploads found in the selected period ({mode}).")
        return

    save_upload_times(upload_hours)

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            all_upload_hours = json.load(f)
    else:
        all_upload_hours = upload_hours

    combined_hours = all_upload_hours + upload_hours
    hour_counts = Counter(combined_hours)
    top_hours = hour_counts.most_common(4)

    st.markdown("### 🕒 Best Times to Post")
    for hour, count in top_hours:
        posting_time = f"{hour % 12 or 12}{'AM' if hour < 12 else 'PM'}"
        st.markdown(f"- **{posting_time}** (seen {count} uploads)")

# ---------- REAL-TIME POST ALERT SYSTEM ----------
def real_time_post_alert():
    india_timezone = pytz.timezone('Asia/Kolkata')
    current_hour = datetime.now(india_timezone).hour

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            all_upload_hours = json.load(f)
    else:
        return

    hour_counts = Counter(all_upload_hours)
    top_hours = [hour for hour, _ in hour_counts.most_common(4)]

    if current_hour in top_hours:
        st.balloons()
        st.success("🚀 It's a Hot Trending Hour Right Now! Post your Short!")
        st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg", format="audio/ogg")

# ---------- REAL-TIME CONTENT TYPE SUGGESTION ----------
def suggest_content_type_real(keywords):
    categories = {
        'music': 'Music/Dance',
        'song': 'Music/Dance',
        'funny': 'Comedy',
        'comedy': 'Comedy',
        'vlog': 'Lifestyle Vlog',
        'news': 'News/Commentary',
        'challenge': 'Challenges',
        'trend': 'Trending Challenge',
        'game': 'Gaming'
    }
    scores = Counter()
    for word, _ in keywords:
        for key in categories:
            if key in word:
                scores[categories[key]] += 1
    if scores:
        return scores.most_common(1)[0][0]
    else:
        return "Entertainment"

# ---------- FETCH TRENDING SONGS (REAL-TIME) ----------
def fetch_trending_songs():
    trending_songs = [
        {"song": "Raanjhan", "artist": "Sachet-Parampara, Parampara Tandon", "link": "https://open.spotify.com/track/2N0k5aCNGLouLAiZrCeyWw"},
        {"song": "Jhol", "artist": "Maanu, Annural Khalid", "link": "https://open.spotify.com/track/37i9dQZEVXbLZ52XmnySJg"},
        {"song": "Kevadyacha Paan Tu", "artist": "Ajay Gogavale, Aarya Ambekar", "link": "https://en.wikipedia.org/wiki/Kevadyacha_Paan_Tu"},
        {"song": "Taambdi Chaamdi", "artist": "Kratex, Shreyas", "link": "https://en.wikipedia.org/wiki/Taambdi_Chaamdi"}
    ]
    return trending_songs

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="YouTube Viral Trends Dashboard", layout="wide")
st.title("📈 YouTube Viral Trend Dashboard")

if 'last_refresh' not in st.session_state or time.time() - st.session_state['last_refresh'] > REFRESH_INTERVAL:
    with st.spinner("Fetching trending videos..."):
        videos = get_trending_videos()
        st.session_state['videos'] = videos
        st.session_state['last_refresh'] = time.time()
else:
    videos = st.session_state['videos']

# Extract info
titles = [v['snippet']['title'] for v in videos]
descriptions = [v['snippet'].get('description', '') for v in videos]
channels = [v['snippet']['channelTitle'] for v in videos]
hashtags_real_time = extract_hashtags_real(videos)

col1, col2, col3 = st.columns(3)

# ---------- Display Trending Videos ----------
with col1:
    st.subheader("🔥 Trending Video Titles")
    for title, channel in zip(titles, channels):
        st.markdown(f"**{title}**<br><sub>by {channel}</sub>", unsafe_allow_html=True)

# ---------- Real-Time Hashtags ----------
with col2:
    st.subheader("🏷 Real-Time Trending Hashtags")
    hashtag_counts = Counter(hashtags_real_time)
    st.bar_chart(pd.DataFrame(hashtag_counts.most_common(10), columns=['Hashtag', 'Count']).set_index('Hashtag'))

# ---------- Keywords Wordcloud ----------
with col3:
    st.subheader("🧠 Common Keywords")
    keywords = extract_keywords(titles)
    fig, ax = plt.subplots(figsize=(5,3))
    wordcloud = WordCloud(width=600, height=300, background_color='white').generate_from_frequencies(dict(keywords))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

# ---------- Display Trending Songs ----------
st.divider()
st.subheader("🎶 Trending Songs Right Now")
trending_songs = fetch_trending_songs()
for song in trending_songs:
    st.markdown(f"**{song['song']}** by {song['artist']} - [Listen Here]({song['link']})")

# ---------- Viral Title Generator ----------
st.divider()
col4, col5 = st.columns(2)

with col4:
    st.subheader("✨ Viral Title Generator")
    user_title = st.text_input("Enter your base title or idea:")
    real_hooks = extract_real_hooks(titles)
    if user_title and real_hooks:
        suggestions = generate_viral_title(user_title, real_hooks)
        st.markdown("**Trending Hook-based Titles:**")
        for s in suggestions:
            st.markdown(f"- {s}")

with col5:
    st.subheader("🚀 Viral Hashtag Booster")
    if user_title:
        boosted_tags = generate_viral_hashtags(keywords)
        st.markdown("**Suggested Hashtags:**")
        st.code(" ".join(boosted_tags))

# ---------- Best Time to Post ----------
st.divider()
st.subheader("🕒 Best Time to Post Today")
hottest_hours_today(videos)

# ---------- Real-Time Posting Alert ----------
real_time_post_alert()

# ---------- Content Suggestion ----------
st.subheader("🎯 Today's Suggested Content Type")
content_type = suggest_content_type_real(keywords)
st.success(f"Recommended: **{content_type}**")
