import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
API_KEY = "AIzaSyAw5XhJLxvtZhkK-r24NI9AtdA3FHRdMlg"
REGION_CODE = "IN"
MAX_RESULTS = 25

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

# ---------- EXTRACT REAL HOOKS FROM TRENDING TITLES ----------
def extract_real_hooks(titles):
    hook_candidates = []
    for title in titles:
        parts = re.split(r"[|:;\-\n]", title)
        hook_candidates.extend([part.strip() for part in parts if 5 < len(part.strip()) < 70])
    # Return most common phrases that seem like attention-grabbers
    return list(dict(Counter(hook_candidates).most_common(10)).keys())

# ---------- GENERATE VIRAL TITLES ----------
def generate_viral_title(base_title, real_hooks):
    return [f"{hook} | {base_title}" for hook in real_hooks]

# ---------- GENERATE VIRAL HASHTAGS ----------
def generate_viral_hashtags(keywords):
    base_tags = ["#shorts", "#trending", "#viral"]
    dynamic_tags = [f"#{kw[0]}" for kw in keywords[:5]]
    return base_tags + dynamic_tags

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="YouTube Viral Trends Dashboard", layout="wide")
st.title("📈 YouTube Viral Trend Dashboard")

with st.spinner("Fetching trending videos..."):
    videos = get_trending_videos()

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
