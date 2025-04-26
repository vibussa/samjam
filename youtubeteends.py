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

# ---------- CONFIG ----------
API_KEY = "AIzaSyAw5XhJLxvtZhkK-r24NI9AtdA3FHRdMlg"
REGION_CODE = "IN"
MAX_RESULTS = 25
REFRESH_INTERVAL = 3600  # seconds (1 hour)

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

# ---------- EXTRACT HASHTAGS ----------
def extract_hashtags(text):
    return re.findall(r"#\w+", text)

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

# ---------- BEST TIME TO POST (REAL DATA) ----------
def suggest_best_time(videos):
    india_timezone = pytz.timezone('Asia/Kolkata')
    upload_hours = []

    for v in videos:
        upload_time_utc = v['snippet']['publishedAt']
        upload_time = datetime.fromisoformat(upload_time_utc.replace('Z', '+00:00')).astimezone(india_timezone)
        upload_hours.append(upload_time.hour)

    if not upload_hours:
        st.warning("Couldn't fetch upload times from videos.")
        return

    hour_counts = Counter(upload_hours)
    top_hours = hour_counts.most_common(4)

    st.markdown("### 🕒 Best Times to Post Based on Today's Trending")
    for hour, count in top_hours:
        posting_time = f"{hour % 12 or 12}{'AM' if hour < 12 else 'PM'}"
        st.markdown(f"- **{posting_time}** (seen {count} trending uploads)")

    st.subheader("📊 Upload Time Heatmap")
    hours_series = pd.Series(upload_hours)
    hist = hours_series.value_counts().sort_index()
    fig, ax = plt.subplots()
    hist.plot(kind='bar', ax=ax)
    ax.set_xlabel('Hour of Day (India Time)')
    ax.set_ylabel('Number of Trending Uploads')
    st.pyplot(fig)

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
hashtag_list = [tag for desc in descriptions + titles for tag in extract_hashtags(desc)]

# ---------- Display Trending Videos ----------
st.subheader("🔥 Trending Video Titles")
for title, channel in zip(titles, channels):
    st.markdown(f"""**{title}**  
`by {channel}`""")

# ---------- Hashtags ----------
st.subheader("🏷 Trending Hashtags")
hashtag_counts = Counter(hashtag_list)
st.bar_chart(pd.DataFrame(hashtag_counts.most_common(10), columns=['Hashtag', 'Count']).set_index('Hashtag'))

# ---------- Keywords ----------
st.subheader("🧠 Common Keywords in Titles")
keywords = extract_keywords(titles)
fig, ax = plt.subplots()
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(dict(keywords))
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis("off")
st.pyplot(fig)

# ---------- Viral Title Generator ----------
st.subheader("✨ Viral Title Generator")
user_title = st.text_input("Enter your base title or idea:")
real_hooks = extract_real_hooks(titles)
if user_title and real_hooks:
    suggestions = generate_viral_title(user_title, real_hooks)
    st.markdown("**Trending Hook-based Titles:**")
    for s in suggestions:
        st.markdown(f"- {s}")

# ---------- Viral Hashtag Booster ----------
st.subheader("🚀 Viral Hashtag Booster")
if user_title:
    boosted_tags = generate_viral_hashtags(keywords)
    st.markdown("**Suggested Hashtags:**")
    st.code(" ".join(boosted_tags))

# ---------- Best Time to Post ----------
st.subheader("🕒 Best Time to Post Today")
suggest_best_time(videos)

# ---------- Content Suggestion ----------
st.subheader("🎯 Today's Suggested Content Type")
content_type = suggest_content_type_real(keywords)
st.success(f"Recommended: **{content_type}**")

