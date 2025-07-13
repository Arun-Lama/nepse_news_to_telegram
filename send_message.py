import os
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz

from sharesansar_and_bizmandu import (
    sharesansar_news,
    merolagani_announcement,
    tomorrow_events
)

# --- Load environment variables ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHANNEL_ID")  # e.g., '@yourchannel'
TELEGRAM_MSG_LIMIT = 4096  # Telegram max message length

# --- Fetch DataFrames ---
sharesansar_news_df = sharesansar_news()
merolagani_announcement_df = merolagani_announcement()
tomorrow_events_df = tomorrow_events()

# --- Combine and Format News DataFrame ---
sharesansar_and_bizmandu_news = pd.concat([sharesansar_news_df, bizmandu_news_df])
sharesansar_and_bizmandu_news['Published Date'] = pd.to_datetime(
    sharesansar_and_bizmandu_news['Published Date']
).dt.floor('D')


# --- Split Long Messages into Chunks ---
def split_message(text, limit=TELEGRAM_MSG_LIMIT):
    paragraphs = text.strip().split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= limit:
            current_chunk += para + "\n\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# --- Send Message(s) to Telegram ---
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    messages = split_message(message)
    for i, part in enumerate(messages):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, data=payload)
        if response.ok:
            print(f"✅ Sent part {i + 1}/{len(messages)}")
        else:
            print(f"❌ Failed to send part {i + 1}: {response.text}")


# --- Format Sections ---
def format_news(df, title):
    if df.empty:
        return None
    df = df.sort_values(by="Published Date", ascending=False)
    message = f"<b>{title}</b>\n\n"
    for _, row in df.iterrows():
        news_title = row['News']
        news_url = row['URL']
        message += f"📰 <a href=\"{news_url}\">{news_title}</a>\n\n"
    return message.strip()


def format_merolagani_announcement(df):
    if df.empty:
        return None

    message = "<b>📢 Announcements Today</b>\n\n"
    for _, row in df.iterrows():
        text = row['Announcement']
        url = row.get('URL') or row.get('Link')  # fallback if column name differs

        date_str = row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else 'N/A'

        if pd.notna(url):
            text = f'<a href="{url}">{text}</a>'

        message += f"🏷️ <b>{date_str}</b>: {text}\n\n"

    return message.strip()


def format_tomorrow_events(df):
    if df.empty:
        return None
    message = "<b>📅 Upcoming Events</b>\n\n"
    for _, row in df.iterrows():
        text = row['Upcoming events']
        url = row.get('URL') or row.get('Link')  # fallback if column name differs
        if pd.notna(url):
            text = f'<a href="{url}">{text}</a>'
        message += f"🔔 <b>{row['Date']}</b>: {text}\n"
    return message.strip()


# --- Generate Time-Based Greeting ---
def get_time_based_greeting():
    npt = pytz.timezone("Asia/Kathmandu")
    now = datetime.now(npt)
    hour = now.hour

    if hour < 11:
        return "🌅 <b>Good Morning!</b> Gearing up for the market today? Here's what's happening:\n"
    elif 12 <= hour < 16:
        return "🍛 <b>Lunch Time Update!</b> Take a quick break and catch up on the market buzz:\n"
    elif hour >= 16:
        return "🌇 <b>Market Summary</b>\nHere's what you need to know as the day winds down:\n"
    else:
        return "🕘 <b>Market Update</b>\nHere's the latest:\n"


# --- Construct Messages ---
if sharesansar_and_bizmandu_news.empty:
    news_message = "<b>🗞️ Market News</b>\n\nThere’s no major news today."
else:
    news_message = format_news(sharesansar_and_bizmandu_news, "🗞️ Market News")

if merolagani_announcement_df.empty:
    announcements_message = "<b>📢 Announcements Today</b>\n\nNo new announcements today."
else:
    announcements_message = format_merolagani_announcement(merolagani_announcement_df)

if tomorrow_events_df.empty:
    events_message = "<b>📅 Upcoming Events</b>\n\nNo major events scheduled for tomorrow."
else:
    events_message = format_tomorrow_events(tomorrow_events_df)

# --- Send Greeting + All Non-Empty Messages ---
greeting = get_time_based_greeting()
first_message_sent = False

for msg in [news_message, announcements_message, events_message]:
    if msg:
        if not first_message_sent:
            msg = greeting + "\n" + msg
            first_message_sent = True
        send_telegram_message(msg)
