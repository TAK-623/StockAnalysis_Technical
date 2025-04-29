import feedparser
import os
import json
import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# 環境変数読み込み
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

WP_RSS_URL = "https://www.takstorage.site/feed"
LAST_WP_POST_FILE = "C:/Users/mount/Git/last_wp_post.txt"

def get_last_posted_url():
    if os.path.exists(LAST_WP_POST_FILE):
        with open(LAST_WP_POST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_last_posted_url(url):
    with open(LAST_WP_POST_FILE, "w", encoding="utf-8") as f:
        f.write(url)

def post_to_x_v2_oauth1(content):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Content-Type": "application/json"
    }
    json_data = {"text": content}

    oauth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
    response = requests.post(url, headers=headers, auth=oauth, json=json_data)

    if response.status_code == 201:
        print("✅ 投稿成功！")
    else:
        print("⚠️ 投稿失敗:", response.status_code, response.text)

def main():
    feed = feedparser.parse(WP_RSS_URL)
    if not feed.entries:
        print("⚠️ RSSが取得できません。")
        return

    latest_entry = feed.entries[0]
    latest_url = latest_entry.link
    last_url = get_last_posted_url()

    if latest_url != last_url:
        tweet_text = f"新しいブログ記事を公開しました\n\n{latest_entry.title}\n{latest_url}"
        post_to_x_v2_oauth1(tweet_text)
        save_last_posted_url(latest_url)
    else:
        print("🟡 新着記事はありません。")

if __name__ == "__main__":
    main()
