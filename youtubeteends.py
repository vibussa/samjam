import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
import time
import os
import json

# ---------- CONFIG ----------
API_KEY = "AIzaSyAw5XhJLxvtZhkK-r24NI9AtdA3FHRdMlg"
REGION_CODE = "IN"
MAX_RESULTS = 25
REFRESH_INTERVAL = 3600
HISTORY_FILE = "upload_history.json"

# ---------- YOUTUBE API SETUP ----------
youtube = build('youtube', 'v3', developerKey=API_KEY)

# ---------- FUNCTIONS ----------

def get_trending_videos():
    request = youtube.videos().list(part="snippet,statistics", chart="mostPopular", regionCode=REGION_CODE, maxResults=MAX_RESULTS)
    response = request.execute()
    return response['items']

def extract_hashtags(text):
    return re.findall(r"#\w+", text)

def extract_keywords(titles):
    words = re.findall(r"\b\w+\b", " ".join(titles).lower())
    stopwords = set(pd.read_csv("https://raw.githubusercontent.com/stopwords-iso/stopwords-en/master/stopwords-en.txt", header=None)[0])
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    return Counter(filtered_words).most_common(20)

def extract_real_hooks(titles):
    matches = []
    for title in titles:
        parts = title.split('|')
        for part in parts:
            cleaned = part.strip()
            if len(cleaned.split()) >= 3 and len(cleaned) < 80:
                matches.append(cleaned)
    return list(set(matches))[:7]

def generate_viral_title(base_title, real_hooks):
    return [f"{hook} | {base_title}" for hook in real_hooks]

def generate_viral_hashtags(keywords):
    base_tags = ["#shorts", "#trending", "#viral"]
    dynamic_tags = [f"#{kw[0]}" for kw in keywords[:5]]
    return base_tags + dynamic_tags

def save_upload_times(upload_hours):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []
    history.extend(upload_hours)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def suggest_best_time(videos):
    india_timezone = pytz.timezone('Asia/Kolkata')
    upload_hours = []

    for v in videos:
        upload_time_utc = v['snippet']['publishedAt']
        upload_time = datetime.fromisoformat(upload_time_utc.replace('Z', '+00:00')).astimezone(india_timezone)
        upload_hours.append(upload_time.hour)

    save_upload_times(upload_hours)

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            all_upload_hours = json.load(f)
    else:
        all_upload_hours = upload_hours

    combined_hours = all_upload_hours + upload_hours
    hour_counts = Counter(combined_hours)
    top_hours = hour_counts.most_common(4)

    st.markdown("### 🕒 Best Times")
    for hour, count in top_hours:
        posting_time = f"{hour % 12 or 12}{'AM' if hour < 12 else 'PM'}"
        st.markdown(f"- **{posting_time}** ({count} uploads)")

    hours_series = pd.Series(combined_hours)
    hist = hours_series.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(4,2))
    hist.plot(kind='bar', ax=ax)
    ax.set_xlabel('Hour')
    ax.set_ylabel('Uploads')
    st.pyplot(fig)

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
        st.success("🚀 It's a Hot Trending Hour! Post Now!")
        st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg", format="audio/ogg")

def suggest_content_type_real(keywords):
    categories = {
        'music': 'Music/Dance', 'song': 'Music/Dance',
        'funny': 'Comedy', 'comedy': 'Comedy',
        'vlog': 'Lifestyle Vlog', 'news': 'News/Commentary',
        'challenge': 'Challenges', 'trend': 'Trending Challenge', 'game': 'Gaming'
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

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="YouTube Viral Trends Dashboard", layout="wide")

st.title("📈 YouTube Viral Trends Dashboard")

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
hashtag_list = [tag for desc in descriptions + titles for tag in extract_hashtags(desc)]

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔥 Trending Titles")
    for title, channel in zip(titles[:8], channels[:8]):
        st.markdown(f"**{title}**  \\`by {channel}`")

    st.markdown("### 🧠 Keywords")
    keywords = extract_keywords(titles)
    fig, ax = plt.subplots(figsize=(3,2))
    wordcloud = WordCloud(width=400, height=200, background_color='white').generate_from_frequencies(dict(keywords))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

with col2:
    st.markdown("### 🏷 Hashtags")
    hashtag_counts = Counter(hashtag_list)
    st.bar_chart(pd.DataFrame(hashtag_counts.most_common(10), columns=['Hashtag', 'Count']).set_index('Hashtag'))

    st.markdown("### 🚀 Viral Hashtags")
    user_title = st.text_input("Enter your base title or idea:")
    if user_title:
        boosted_tags = generate_viral_hashtags(keywords)
        st.code(" ".join(boosted_tags))

with col3:
    st.markdown("### ✨ Viral Titles")
    real_hooks = extract_real_hooks(titles)
    if user_title and real_hooks:
        suggestions = generate_viral_title(user_title, real_hooks)
        for s in suggestions:
            st.markdown(f"- {s}")

    st.markdown("### 🎯 Content Type")
    content_type = suggest_content_type_real(keywords)
    st.success(f"Recommended: **{content_type}**")

    st.markdown("### 🕒 Post Timing")
    suggest_best_time(videos)

real_time_post_alert()
