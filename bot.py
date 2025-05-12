# Hourly AI News Video Bot
# Requirements: requests, moviepy, google-auth, google-api-python-client, pytube, gTTS

import os
import requests
from gtts import gTTS
from moviepy.editor import *
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import json

print("Starting the bot...")

# --- 1. Fetch News from NewsAPI ---
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_ENDPOINT = f'https://newsapi.org/v2/top-headlines?country=us&pageSize=1&apiKey={NEWS_API_KEY}'

response = requests.get(NEWS_ENDPOINT)
news_data = response.json()
article = news_data['articles'][0]
title = article['title']
description = article['description'] or ''
content = f"{title}. {description}"

# --- 2. Generate Voiceover ---
tts = gTTS(text=content, lang='en')
voiceover_path = "voiceover.mp3"
tts.save(voiceover_path)

# --- 3. Generate Video ---
background_clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=20)

text_clip = TextClip(content, fontsize=40, color='white', size=(1200, None), method='caption')\
    .set_position('center').set_duration(20)

voiceover = AudioFileClip(voiceover_path)
video = CompositeVideoClip([background_clip, text_clip]).set_audio(voiceover)
video_path = "news_video.mp4"
video.write_videofile(video_path, fps=24)

# --- 4. Upload to YouTube ---
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')


with open("temp_service_account.json", "w") as f:
    f.write(SERVICE_ACCOUNT_JSON)

auth_credentials = service_account.Credentials.from_service_account_file(
    "temp_service_account.json", scopes=SCOPES)

youtube = build("youtube", "v3", credentials=auth_credentials)

request_body = {
    'snippet': {
        'categoryId': '25',
        'title': f"{title} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        'description': description,
        'tags': ['news', 'AI', 'daily news']
    },
    'status': {
        'privacyStatus': 'public'
    }
}

media = MediaFileUpload(video_path, mimetype='video/*', resumable=True)
response_upload = youtube.videos().insert(
    part='snippet,status',
    body=request_body,
    media_body=media
).execute()

print(f"Uploaded video: https://youtube.com/watch?v={response_upload['id']}")
